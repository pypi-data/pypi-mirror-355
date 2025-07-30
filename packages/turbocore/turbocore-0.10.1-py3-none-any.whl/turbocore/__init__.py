import os
import sys
import inspect
import site


def this_sitepackages():
    print(site.getusersitepackages())
    print(sys.path)


def this_platform():
    if sys.platform.upper().startswith("DARWIN"):
        return "m"
    if sys.platform.upper().startswith("WIN32"):
        return "w"
    if sys.platform.upper().startswith("LINUX"):
        return "l"
    return "u"


def cli_this(module_name, f_prefix="", build_manual=False):

    program_name = sys.argv[0].split(os.sep)[-1]
    all_f_map = {}
    for m,o in inspect.getmembers(sys.modules[module_name]):
        if inspect.isfunction(o) and m.startswith(f_prefix):
            f_name = m[len(f_prefix):]
            all_f_map[f_name] = o
    for f_current in sorted(all_f_map.keys()):
        f_sig = str(inspect.signature(all_f_map[f_current])).replace("(", "").replace(")", "").upper()
        f_sig = [ "<" + xx.strip() + ">" for xx in f_sig.split(" ") if xx.strip() != "" ]
        f_sig = " ".join(f_sig).replace(",", "")
        f_doc = inspect.getdoc(all_f_map[f_current])
        f_docfull = inspect.getdoc(all_f_map[f_current])
        if f_docfull == None:
            f_docfull = ""
        f_docfull = f_docfull.split("\n")
        if f_doc == None:
            f_doc = "undocumented method"
        f_doc = f_doc.split("\n")[0].strip()




    if build_manual:
        if program_name.endswith("__main__.py"):
            program_name = os.environ.get("BASH_SRC", "PROGRAM").split(os.sep)[-1]

        lines = ["Syntax:", ""]
        for f_current in sorted(all_f_map.keys()):
            f_sig = str(inspect.signature(all_f_map[f_current])).replace("(", "").replace(")", "").upper()
            f_sig = [ "<" + xx.strip() + ">" for xx in f_sig.split(" ") if xx.strip() != "" ]
            f_sig = " ".join(f_sig).replace(",", "")

            f_doc = inspect.getdoc(all_f_map[f_current])
            if f_doc == None:
                f_doc = ""
            f_doc = f_doc.split("\n")[0].strip()

            f_docfull = inspect.getdoc(all_f_map[f_current])
            if f_docfull == None:
                f_docfull = "undocumented function %s\nundocumented" % f_current
            f_docfull = f_docfull.split("\n")

            lines.append("  %s %s %s" % (program_name, f_current, f_sig))
            line_idx = 1
            lines.append("")
            for doc_line in f_docfull:
                if line_idx in [1,2]:
                    lines.append("    " + "="*(3+len(f_docfull[0])))
                lines.append("    >> %s" % doc_line)
                line_idx+=1
            lines.append("")
            lines.append("")
        return "\n".join(lines)

    if len(sys.argv) <= 1:
        print("No args given")
        print("")
        print(cli_this(module_name, f_prefix, build_manual=True))
        sys.exit(1)
        return

    action = sys.argv[1]
    help_check = action.strip().replace("-", "")
    if help_check == "h" or help_check == "help":
        print(cli_this(module_name, f_prefix, build_manual=True))
        sys.exit(0)

    opts = sys.argv[2:]
    f_actual = None

    for m,o in inspect.getmembers(sys.modules[module_name]):
        if inspect.isfunction(o) and m.startswith(f_prefix) and m == f_prefix+action:
            f_actual = o
            break

    if f_actual is not None:
        # f_actual()
        #print("would call %s with %s" % (f_actual, str(opts)))
        f_actual(*opts)
        sys.exit(0)
    else:
        print("unknown action %s" % action)
        sys.exit(1)
