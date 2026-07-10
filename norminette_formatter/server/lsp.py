"""LSP server — the bridge between the core formatter and any editor.

Uses pygls (Python Language Server) to expose diagnostics, code actions,
and formatting via the standard Language Server Protocol.
"""

from __future__ import annotations

import logging
from pathlib import Path

from pygls.lsp.server import LanguageServer
from lsprotocol import types

from ..core import NorminetteFormatter
from ..core.diagnostics import Diagnostic, Severity
from ..core.fixer import compute_fixes

logger = logging.getLogger(__name__)

server = LanguageServer("norminette-formatter", "0.1.0")
formatter = NorminetteFormatter()


def _severity_to_lsp(severity: Severity) -> types.DiagnosticSeverity:
    if severity == Severity.ERROR:
        return types.DiagnosticSeverity.Error
    return types.DiagnosticSeverity.Warning


def _diagnostic_to_lsp(diag: Diagnostic) -> types.Diagnostic:
    line = max(0, diag.line - 1)
    col = max(0, diag.col - 1)
    return types.Diagnostic(
        range=types.Range(
            start=types.Position(line=line, character=col),
            end=types.Position(line=line, character=col + 1),
        ),
        message=f"[{diag.code}] {diag.message}",
        severity=_severity_to_lsp(diag.severity),
        source="norminette",
        code=diag.code,
    )


def _publish_diagnostics(uri: str, source: str):
    file_path = uri.replace("file://", "")
    try:
        diagnostics = formatter.diagnose_source(source, file_path)
        lsp_diags = [_diagnostic_to_lsp(d) for d in diagnostics]
        server.publish_diagnostics(uri, lsp_diags)
    except RuntimeError as e:
        logger.error(f"norminette error: {e}")
        server.publish_diagnostics(uri, [])


@server.feature(types.TEXT_DOCUMENT_DID_OPEN)
def did_open(params: types.DidOpenTextDocumentParams):
    uri = params.text_document.uri
    source = params.text_document.text
    _publish_diagnostics(uri, source)


@server.feature(types.TEXT_DOCUMENT_DID_SAVE)
def did_save(params: types.DidSaveTextDocumentParams):
    uri = params.text_document.uri
    file_path = uri.replace("file://", "")
    source = Path(file_path).read_text()
    _publish_diagnostics(uri, source)


@server.feature(types.TEXT_DOCUMENT_DID_CHANGE)
def did_change(params: types.DidChangeTextDocumentParams):
    uri = params.text_document.uri
    if params.content_changes:
        source = params.content_changes[-1].text
        _publish_diagnostics(uri, source)


@server.feature(types.TEXT_DOCUMENT_CODE_ACTION)
def code_action(params: types.CodeActionParams) -> list[types.CodeAction]:
    uri = params.text_document.uri
    file_path = uri.replace("file://", "")

    doc = server.workspace.get_text_document(uri)
    source = doc.source
    diagnostics = formatter.diagnose_source(source, file_path)

    range_start = params.range.start.line + 1
    range_end = params.range.end.line + 1
    relevant = [d for d in diagnostics if range_start <= d.line <= range_end]

    if not relevant:
        return []

    actions = []

    fixes = compute_fixes(source, relevant)
    for fix in fixes:
        line_idx = fix.line - 1
        edit = types.TextEdit(
            range=types.Range(
                start=types.Position(line=line_idx, character=0),
                end=types.Position(line=line_idx + 1, character=0),
            ),
            new_text=fix.new_text if fix.new_text.endswith("\n") else fix.new_text + "\n",
        )
        action = types.CodeAction(
            title=f"Fix: {fix.description}",
            kind=types.CodeActionKind.QuickFix,
            edit=types.WorkspaceEdit(
                changes={uri: [edit]}
            ),
        )
        actions.append(action)

    if relevant:
        all_edits = []
        all_fixes = compute_fixes(source, diagnostics)
        for fix in all_fixes:
            line_idx = fix.line - 1
            all_edits.append(
                types.TextEdit(
                    range=types.Range(
                        start=types.Position(line=line_idx, character=0),
                        end=types.Position(line=line_idx + 1, character=0),
                    ),
                    new_text=fix.new_text if fix.new_text.endswith("\n") else fix.new_text + "\n",
                )
            )
        if all_edits:
            fix_all_action = types.CodeAction(
                title="Fix all norminette errors",
                kind=types.CodeActionKind.SourceFixAll,
                edit=types.WorkspaceEdit(changes={uri: all_edits}),
            )
            actions.append(fix_all_action)

    return actions


@server.feature(types.TEXT_DOCUMENT_FORMATTING)
def formatting(params: types.DocumentFormattingParams) -> list[types.TextEdit]:
    uri = params.text_document.uri
    file_path = uri.replace("file://", "")

    doc = server.workspace.get_text_document(uri)
    source = doc.source
    result = formatter.fix_source(source, file_path)

    if result.fixed == result.original:
        return []

    lines = source.splitlines(keepends=True)
    return [
        types.TextEdit(
            range=types.Range(
                start=types.Position(line=0, character=0),
                end=types.Position(line=len(lines), character=0),
            ),
            new_text=result.fixed,
        )
    ]


def start_server():
    server.start_io()
