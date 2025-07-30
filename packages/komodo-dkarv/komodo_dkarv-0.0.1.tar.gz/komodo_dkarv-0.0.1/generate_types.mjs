import { exec } from "child_process";
import { readFileSync, writeFileSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

console.log("generating python types...");

const gen_command =
  "RUST_BACKTRACE=1 typeshare . --lang=python --output-file=./client/core/py/src/komodo_dkarv/types.py";

exec(gen_command, (error, _stdout, _stderr) => {
  if (error) {
    console.error(error);
    return;
  }
  console.log("generated types using typeshare");
  //fix_types();
  console.log("finished.");
});

function fix_types() {
  const types_path = __dirname + "/src/types.ts";
  const contents = readFileSync(types_path);
  const fixed = contents
    .toString()
    // Replace Variants
    .replaceAll("ResourceTargetVariant", 'ResourceTarget["type"]')
    .replaceAll("AlerterEndpointVariant", 'AlerterEndpoint["type"]')
    .replaceAll("AlertDataVariant", 'AlertData["type"]')
    .replaceAll("ServerTemplateConfigVariant", 'ServerTemplateConfig["type"]')
    // Add '| string' to env vars
    .replaceAll("EnvironmentVar[]", "EnvironmentVar[] | string")
    .replaceAll("IndexSet", "Array")
    .replaceAll(
      ": PermissionLevelAndSpecifics",
      ": PermissionLevelAndSpecifics | PermissionLevel"
    )
    .replaceAll(
      ", PermissionLevelAndSpecifics",
      ", PermissionLevelAndSpecifics | PermissionLevel"
    )
    .replaceAll("IndexMap", "Record");
  writeFileSync(types_path, fixed);
}
