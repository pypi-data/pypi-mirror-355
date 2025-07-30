define-command lsp-diag-set %{
    evaluate-commands %sh{
        {
            printf 'set %s\n' "$kak_opt_lsp_inline_diagnostics" >"$kak_opt_diagpipe_in"
            read result < "$kak_opt_diagpipe_out"
            if [ "$result" != "ok" ]; then
                cmd=$(printf "eval -try-client '$kak_client' -verbatim info -title lsp-diag 'failed to parse diagnostics'")
                echo "$cmd" | kak -p ${kak_session}
            fi
        } </dev/null >/dev/null 2>&1 &
    }
}

define-command -params 2 lsp-diag-query %{
    evaluate-commands %sh{
        printf 'query %s %s\n' "$1" "$2" >"$kak_opt_diagpipe_in"
        read result < "$kak_opt_diagpipe_out"
        if [ "$result" = "true" ]; then
            echo "trigger-user-hook lsp-diag-hover-true"
        else
            echo "trigger-user-hook lsp-diag-hover-false"
        fi
    }
}

hook global KakEnd .* %{
    nop %sh{
        printf 'exit\n' >"$kak_opt_diagpipe_in"
        read result < "$kak_opt_diagpipe_out"
    }
}

declare-option -hidden bool lsp_diags_enabled false

try %{ define-command -hidden true nop }
try %{ define-command -hidden false fail }

define-command lsp-diag-hover-enable %{
    lsp-diag-set

    hook -group lsp-diag window User lsp-diag-hover-false %{
        try %{
            %opt{lsp_diags_enabled}
            try %{
                lsp-inlay-diagnostics-disable window
                set-option window lsp_diags_enabled false
            }
        } 
    }

    hook -group lsp-diag window User lsp-diag-hover-true %{
        try %{
            %opt{lsp_diags_enabled}
        } catch %{
            try %{
                lsp-inlay-diagnostics-enable window
                set-option window lsp_diags_enabled true
            }
        }
    }
    hook -group lsp-diag window NormalIdle .* %{
        lsp-diag-query %val{cursor_line} %val{cursor_column}
    }
    hook -group lsp-diag window WinSetOption lsp_inline_diagnostics=.* %{
        lsp-diag-set
    }
    hook -group lsp-diag window ModeChange .+:normal:insert %{
        try %{ lsp-inlay-diagnostics-disable window }
    }
}
define-command lsp-diag-hover-disable %{
    remove-hooks window lsp-diag
    try %{
        lsp-inlay-diagnostics-disable window
        set-option window lsp_diags_enabled false
    }
}

