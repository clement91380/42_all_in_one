const { LanguageClient, TransportKind } = require("vscode-languageclient/node");
const vscode = require("vscode");

let client;

function activate(context) {
  const config = vscode.workspace.getConfiguration("norminetteFormatter");
  const command = config.get("serverPath", "naf");

  const serverOptions = {
    command: command,
    args: ["server"],
    transport: TransportKind.stdio,
  };

  const clientOptions = {
    documentSelector: [
      { scheme: "file", language: "c" },
      { scheme: "file", language: "cpp" },
    ],
  };

  client = new LanguageClient(
    "norminetteFormatter",
    "Norminette Formatter",
    serverOptions,
    clientOptions
  );

  client.start();

  if (config.get("autoFixOnSave", false)) {
    vscode.workspace.onDidSaveTextDocument(async (doc) => {
      if (doc.languageId === "c" || doc.languageId === "cpp") {
        await vscode.commands.executeCommand(
          "editor.action.formatDocument"
        );
      }
    });
  }

  const fixAllCmd = vscode.commands.registerCommand(
    "norminetteFormatter.fixAll",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (editor) {
        await vscode.commands.executeCommand(
          "editor.action.formatDocument"
        );
      }
    }
  );

  context.subscriptions.push(fixAllCmd);
}

function deactivate() {
  if (client) {
    return client.stop();
  }
}

module.exports = { activate, deactivate };
