;;; norminette-formatter.el --- Norminette auto-formatter via LSP -*- lexical-binding: t; -*-

;; Requires: eglot (built-in Emacs 29+) or lsp-mode

;;; Setup with eglot (recommended, built-in):

(with-eval-after-load 'eglot
  (add-to-list 'eglot-server-programs
               '(c-mode . ("naf" "server"))))

;; Auto-start eglot for C files:
;; (add-hook 'c-mode-hook 'eglot-ensure)

;;; Setup with lsp-mode:

(with-eval-after-load 'lsp-mode
  (lsp-register-client
   (make-lsp-client
    :new-connection (lsp-stdio-connection '("naf" "server"))
    :activation-fn (lsp-activate-on "c")
    :server-id 'norminette-formatter)))

;;; Manual commands (work without LSP):

(defun norminette-check ()
  "Run norminette check on current buffer."
  (interactive)
  (compile (format "naf check %s" (shell-quote-argument buffer-file-name))))

(defun norminette-fix ()
  "Run norminette auto-fix on current buffer."
  (interactive)
  (let ((file (buffer-file-name)))
    (shell-command (format "naf fix %s" (shell-quote-argument file)))
    (revert-buffer t t t)))

(provide 'norminette-formatter)
;;; norminette-formatter.el ends here
