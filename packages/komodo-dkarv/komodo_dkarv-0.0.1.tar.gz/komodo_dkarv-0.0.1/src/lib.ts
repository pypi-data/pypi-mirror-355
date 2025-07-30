import {
  AuthResponses,
  ExecuteResponses,
  ReadResponses,
  UserResponses,
  WriteResponses,
} from "./responses.js";
import {
  AuthRequest,
  BatchExecutionResponse,
  ConnectContainerExecQuery,
  ConnectDeploymentExecQuery,
  ConnectStackExecQuery,
  ConnectTerminalQuery,
  ExecuteRequest,
  ExecuteTerminalBody,
  ReadRequest,
  Update,
  UpdateListItem,
  UpdateStatus,
  UserRequest,
  WriteRequest,
  WsLoginMessage,
} from "./types.js";

export * as Types from "./types.js";

export type InitOptions =
  | { type: "jwt"; params: { jwt: string } }
  | { type: "api-key"; params: { key: string; secret: string } };

export class CancelToken {
  cancelled: boolean;
  constructor() {
    this.cancelled = false;
  }
  cancel() {
    this.cancelled = true;
  }
}

export type ContainerExecQuery =
  | {
      type: "container";
      query: ConnectContainerExecQuery;
    }
  | {
      type: "deployment";
      query: ConnectDeploymentExecQuery;
    }
  | {
      type: "stack";
      query: ConnectStackExecQuery;
    };

export type TerminalCallbacks = {
  on_message?: (e: MessageEvent<any>) => void;
  on_login?: () => void;
  on_open?: () => void;
  on_close?: () => void;
};

/** Initialize a new client for Komodo */
export function KomodoClient(url: string, options: InitOptions) {
  const state = {
    jwt: options.type === "jwt" ? options.params.jwt : undefined,
    key: options.type === "api-key" ? options.params.key : undefined,
    secret: options.type === "api-key" ? options.params.secret : undefined,
  };

  const request = <Params, Res>(
    path: "/auth" | "/user" | "/read" | "/execute" | "/write",
    type: string,
    params: Params
  ): Promise<Res> =>
    new Promise(async (res, rej) => {
      try {
        let response = await fetch(`${url}${path}/${type}`, {
          method: "POST",
          body: JSON.stringify(params),
          headers: {
            ...(state.jwt
              ? {
                  authorization: state.jwt,
                }
              : state.key && state.secret
              ? {
                  "x-api-key": state.key,
                  "x-api-secret": state.secret,
                }
              : {}),
            "content-type": "application/json",
          },
        });
        if (response.status === 200) {
          const body: Res = await response.json();
          res(body);
        } else {
          try {
            const result = await response.json();
            rej({ status: response.status, result });
          } catch (error) {
            rej({
              status: response.status,
              result: {
                error: "Failed to get response body",
                trace: [JSON.stringify(error)],
              },
              error,
            });
          }
        }
      } catch (error) {
        rej({
          status: 1,
          result: {
            error: "Request failed with error",
            trace: [JSON.stringify(error)],
          },
          error,
        });
      }
    });

  const auth = async <
    T extends AuthRequest["type"],
    Req extends Extract<AuthRequest, { type: T }>
  >(
    type: T,
    params: Req["params"]
  ) =>
    await request<Req["params"], AuthResponses[Req["type"]]>(
      "/auth",
      type,
      params
    );

  const user = async <
    T extends UserRequest["type"],
    Req extends Extract<UserRequest, { type: T }>
  >(
    type: T,
    params: Req["params"]
  ) =>
    await request<Req["params"], UserResponses[Req["type"]]>(
      "/user",
      type,
      params
    );

  const read = async <
    T extends ReadRequest["type"],
    Req extends Extract<ReadRequest, { type: T }>
  >(
    type: T,
    params: Req["params"]
  ) =>
    await request<Req["params"], ReadResponses[Req["type"]]>(
      "/read",
      type,
      params
    );

  const write = async <
    T extends WriteRequest["type"],
    Req extends Extract<WriteRequest, { type: T }>
  >(
    type: T,
    params: Req["params"]
  ) =>
    await request<Req["params"], WriteResponses[Req["type"]]>(
      "/write",
      type,
      params
    );

  const execute = async <
    T extends ExecuteRequest["type"],
    Req extends Extract<ExecuteRequest, { type: T }>
  >(
    type: T,
    params: Req["params"]
  ) =>
    await request<Req["params"], ExecuteResponses[Req["type"]]>(
      "/execute",
      type,
      params
    );

  const execute_and_poll = async <
    T extends ExecuteRequest["type"],
    Req extends Extract<ExecuteRequest, { type: T }>
  >(
    type: T,
    params: Req["params"]
  ) => {
    const res = await execute(type, params);
    // Check if its a batch of updates or a single update;
    if (Array.isArray(res)) {
      const batch = res as any as BatchExecutionResponse;
      return await Promise.all(
        batch.map(async (item) => {
          if (item.status === "Err") {
            return item;
          }
          return await poll_update_until_complete(item.data._id?.$oid!);
        })
      );
    } else {
      // it is a single update
      const update = res as any as Update;
      return await poll_update_until_complete(update._id?.$oid!);
    }
  };

  const poll_update_until_complete = async (update_id: string) => {
    while (true) {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      const update = await read("GetUpdate", { id: update_id });
      if (update.status === UpdateStatus.Complete) {
        return update;
      }
    }
  };

  const core_version = () => read("GetVersion", {}).then((res) => res.version);

  const get_update_websocket = ({
    on_update,
    on_login,
    on_open,
    on_close,
  }: {
    on_update: (update: UpdateListItem) => void;
    on_login?: () => void;
    on_open?: () => void;
    on_close?: () => void;
  }) => {
    const ws = new WebSocket(url.replace("http", "ws") + "/ws/update");

    // Handle login on websocket open
    ws.addEventListener("open", () => {
      on_open?.();
      const login_msg: WsLoginMessage =
        options.type === "jwt"
          ? {
              type: "Jwt",
              params: {
                jwt: options.params.jwt,
              },
            }
          : {
              type: "ApiKeys",
              params: {
                key: options.params.key,
                secret: options.params.secret,
              },
            };
      ws.send(JSON.stringify(login_msg));
    });

    ws.addEventListener("message", ({ data }: MessageEvent) => {
      if (data == "LOGGED_IN") return on_login?.();
      on_update(JSON.parse(data));
    });

    if (on_close) {
      ws.addEventListener("close", on_close);
    }

    return ws;
  };

  const subscribe_to_update_websocket = async ({
    on_update,
    on_open,
    on_login,
    on_close,
    retry = true,
    retry_timeout_ms = 5_000,
    cancel = new CancelToken(),
    on_cancel,
  }: {
    on_update: (update: UpdateListItem) => void;
    on_login?: () => void;
    on_open?: () => void;
    on_close?: () => void;
    retry?: boolean;
    retry_timeout_ms?: number;
    cancel?: CancelToken;
    on_cancel?: () => void;
  }) => {
    while (true) {
      if (cancel.cancelled) {
        on_cancel?.();
        return;
      }

      try {
        const ws = get_update_websocket({
          on_open,
          on_login,
          on_update,
          on_close,
        });

        // This while loop will end when the socket is closed
        while (
          ws.readyState !== WebSocket.CLOSING &&
          ws.readyState !== WebSocket.CLOSED
        ) {
          if (cancel.cancelled) ws.close();
          // Sleep for a bit before checking for websocket closed
          await new Promise((resolve) => setTimeout(resolve, 500));
        }

        if (retry) {
          // Sleep for a bit before retrying connection to avoid spam.
          await new Promise((resolve) => setTimeout(resolve, retry_timeout_ms));
        } else {
          return;
        }
      } catch (error) {
        console.error(error);
        if (retry) {
          // Sleep for a bit before retrying, maybe Komodo Core is down temporarily.
          await new Promise((resolve) => setTimeout(resolve, retry_timeout_ms));
        } else {
          return;
        }
      }
    }
  };

  const connect_terminal = ({
    query,
    on_message,
    on_login,
    on_open,
    on_close,
  }: {
    query: ConnectTerminalQuery;
  } & TerminalCallbacks) => {
    const url_query = new URLSearchParams(
      query as any as Record<string, string>
    ).toString();
    const ws = new WebSocket(
      url.replace("http", "ws") + "/ws/terminal?" + url_query
    );
    // Handle login on websocket open
    ws.onopen = () => {
      const login_msg: WsLoginMessage =
        options.type === "jwt"
          ? {
              type: "Jwt",
              params: {
                jwt: options.params.jwt,
              },
            }
          : {
              type: "ApiKeys",
              params: {
                key: options.params.key,
                secret: options.params.secret,
              },
            };
      ws.send(JSON.stringify(login_msg));
      on_open?.();
    };

    ws.onmessage = (e) => {
      if (e.data == "LOGGED_IN") {
        ws.binaryType = "arraybuffer";
        ws.onmessage = (e) => on_message?.(e);
        on_login?.();
        return;
      } else {
        on_message?.(e);
      }
    };

    ws.onclose = () => on_close?.();

    return ws;
  };

  const connect_container_exec = ({
    query: { type, query },
    on_message,
    on_login,
    on_open,
    on_close,
  }: {
    query: ContainerExecQuery;
  } & TerminalCallbacks) => {
    const url_query = new URLSearchParams(
      query as any as Record<string, string>
    ).toString();
    const ws = new WebSocket(
      url.replace("http", "ws") + `/ws/${type}/terminal?` + url_query
    );
    // Handle login on websocket open
    ws.onopen = () => {
      const login_msg: WsLoginMessage =
        options.type === "jwt"
          ? {
              type: "Jwt",
              params: {
                jwt: options.params.jwt,
              },
            }
          : {
              type: "ApiKeys",
              params: {
                key: options.params.key,
                secret: options.params.secret,
              },
            };
      ws.send(JSON.stringify(login_msg));
      on_open?.();
    };

    ws.onmessage = (e) => {
      if (e.data == "LOGGED_IN") {
        ws.binaryType = "arraybuffer";
        ws.onmessage = (e) => on_message?.(e);
        on_login?.();
        return;
      } else {
        on_message?.(e);
      }
    };

    ws.onclose = () => on_close?.();

    return ws;
  };

  const execute_terminal_stream = (request: ExecuteTerminalBody) =>
    new Promise<AsyncIterable<string>>(async (res, rej) => {
      try {
        let response = await fetch(url + "/terminal/execute", {
          method: "POST",
          body: JSON.stringify(request),
          headers: {
            ...(state.jwt
              ? {
                  authorization: state.jwt,
                }
              : state.key && state.secret
              ? {
                  "x-api-key": state.key,
                  "x-api-secret": state.secret,
                }
              : {}),
            "content-type": "application/json",
          },
        });
        if (response.status === 200) {
          if (response.body) {
            const stream = response.body
              .pipeThrough(new TextDecoderStream("utf-8"))
              .pipeThrough(
                new TransformStream<string, string>({
                  start(_controller) {
                    this.tail = "";
                  },
                  transform(chunk, controller) {
                    const data = this.tail + chunk; // prepend any carry‑over
                    const parts = data.split(/\r?\n/); // split on CRLF or LF
                    this.tail = parts.pop()!; // last item may be incomplete
                    for (const line of parts) controller.enqueue(line);
                  },
                  flush(controller) {
                    if (this.tail) controller.enqueue(this.tail); // final unterminated line
                  },
                } as Transformer<string, string> & { tail: string })
              );
            res(stream);
          } else {
            rej({
              status: response.status,
              result: { error: "No response body", trace: [] },
            });
          }
        } else {
          try {
            const result = await response.json();
            rej({ status: response.status, result });
          } catch (error) {
            rej({
              status: response.status,
              result: {
                error: "Failed to get response body",
                trace: [JSON.stringify(error)],
              },
              error,
            });
          }
        }
      } catch (error) {
        rej({
          status: 1,
          result: {
            error: "Request failed with error",
            trace: [JSON.stringify(error)],
          },
          error,
        });
      }
    });

  const execute_terminal = async (
    request: ExecuteTerminalBody,
    callbacks?: {
      onLine?: (line: string) => void | Promise<void>;
      onFinish?: (code: string) => void | Promise<void>;
    }
  ) => {
    const stream = await execute_terminal_stream(request);
    for await (const line of stream) {
      if (line.startsWith("__KOMODO_EXIT_CODE")) {
        await callbacks?.onFinish?.(line.split(":")[1]);
        return;
      } else {
        await callbacks?.onLine?.(line);
      }
    }
    // This is hit if no __KOMODO_EXIT_CODE is sent, ie early exit
    await callbacks?.onFinish?.("Early exit without code");
  };

  return {
    /**
     * Call the `/auth` api.
     *
     * ```
     * const login_options = await komodo.auth("GetLoginOptions", {});
     * ```
     *
     * https://docs.rs/komodo_client/latest/komodo_client/api/auth/index.html
     */
    auth,
    /**
     * Call the `/user` api.
     *
     * ```
     * const { key, secret } = await komodo.user("CreateApiKey", {
     *   name: "my-api-key"
     * });
     * ```
     *
     * https://docs.rs/komodo_client/latest/komodo_client/api/user/index.html
     */
    user,
    /**
     * Call the `/read` api.
     *
     * ```
     * const stack = await komodo.read("GetStack", {
     *   stack: "my-stack"
     * });
     * ```
     *
     * https://docs.rs/komodo_client/latest/komodo_client/api/read/index.html
     */
    read,
    /**
     * Call the `/write` api.
     *
     * ```
     * const build = await komodo.write("UpdateBuild", {
     *   id: "my-build",
     *   config: {
     *     version: "1.0.4"
     *   }
     * });
     * ```
     *
     * https://docs.rs/komodo_client/latest/komodo_client/api/write/index.html
     */
    write,
    /**
     * Call the `/execute` api.
     *
     * ```
     * const update = await komodo.execute("DeployStack", {
     *   stack: "my-stack"
     * });
     * ```
     *
     * NOTE. These calls return immediately when the update is created, NOT when the execution task finishes.
     * To have the call only return when the task finishes, use [execute_and_poll_until_complete].
     *
     * https://docs.rs/komodo_client/latest/komodo_client/api/execute/index.html
     */
    execute,
    /**
     * Call the `/execute` api, and poll the update until the task has completed.
     *
     * ```
     * const update = await komodo.execute_and_poll("DeployStack", {
     *   stack: "my-stack"
     * });
     * ```
     *
     * https://docs.rs/komodo_client/latest/komodo_client/api/execute/index.html
     */
    execute_and_poll,
    /**
     * Poll an Update (returned by the `execute` calls) until the `status` is `Complete`.
     * https://docs.rs/komodo_client/latest/komodo_client/entities/update/struct.Update.html#structfield.status.
     */
    poll_update_until_complete,
    /** Returns the version of Komodo Core the client is calling to. */
    core_version,
    /**
     * Connects to update websocket, performs login and attaches handlers,
     * and returns the WebSocket handle.
     */
    get_update_websocket,
    /**
     * Subscribes to the update websocket with automatic reconnect loop.
     *
     * Note. Awaiting this method will never finish.
     */
    subscribe_to_update_websocket,
    /**
     * Subscribes to terminal io over websocket message,
     * for use with xtermjs.
     */
    connect_terminal,
    /**
     * Subscribes to container exec io over websocket message,
     * for use with xtermjs. Can connect to Deployment, Stack,
     * or any container on a Server. The permission used to allow the connection
     * depends on `query.type`.
     */
    connect_container_exec,
    /**
     * Executes a command on a given Server / terminal,
     * and returns a stream to process the output as it comes in.
     *
     * Note. The final line of the stream will usually be
     * `__KOMODO_EXIT_CODE__:0`. The number
     * is the exit code of the command.
     *
     * If this line is NOT present, it means the stream
     * was terminated early, ie like running `exit`.
     *
     * ```ts
     * const stream = await komodo.execute_terminal_stream({
     *   server: "my-server",
     *   terminal: "name",
     *   command: 'for i in {1..3}; do echo "$i"; sleep 1; done',
     * });
     *
     * for await (const line of stream) {
     *   console.log(line);
     * }
     * ```
     */
    execute_terminal_stream,
    /**
     * Executes a command on a given Server / terminal,
     * and gives a callback to handle the output as it comes in.
     *
     * ```ts
     * const stream = await komodo.execute_terminal(
     *   {
     *     server: "my-server",
     *     terminal: "name",
     *     command: 'for i in {1..3}; do echo "$i"; sleep 1; done',
     *   },
     *   {
     *     onLine: (line) => console.log(line),
     *     onFinish: (code) => console.log("Finished:", code),
     *   }
     * );
     * ```
     */
    execute_terminal,
  };
}
