# MIT License
#
# Copyright (c) 2025 ericsmacedo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Lexers for hardware descriptor languages (pygments.lexers.hdl).

:copyright: Copyright 2006-2024 by the Pygments team, see AUTHORS.
:license: BSD, see LICENSE for details.
"""

import logging
import re

from pygments.lexer import ExtendedRegexLexer, LexerContext, bygroups, default, include, words
from pygments.token import (
    Comment,
    Error,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
    Token,
    Whitespace,
    _TokenType,
)

from ._token import Module, Port

__all__ = ["SystemVerilogLexer"]

# Create a LOGGER for this module
LOGGER = logging.getLogger(__name__)

punctuation = (r"[()\[\],.;\'$]", Punctuation)


preproc = (r"`(ifdef|ifndef|else|endif|define|undef)\b\s*?\w+", Comment.Preproc)

builtin_tup = (
    # Simulation control tasks (20.2)
    "$exit",
    "$finish",
    "$stop",
    # Simulation time functions (20.3)
    "$realtime",
    "$stime",
    "$time",
    # Timescale tasks (20.4)
    "$printtimescale",
    "$timeformat",
    # Conversion functions
    "$bitstoreal",
    "$bitstoshortreal",
    "$cast",
    "$itor",
    "$realtobits",
    "$rtoi",
    "$shortrealtobits",
    "$signed",
    "$unsigned",
    # Data query functions (20.6)
    "$bits",
    "$isunbounded",
    "$typename",
    # Array query functions (20.7)
    "$dimensions",
    "$high",
    "$increment",
    "$left",
    "$low",
    "$right",
    "$size",
    "$unpacked_dimensions",
    # Math functions (20.8)
    "$acos",
    "$acosh",
    "$asin",
    "$asinh",
    "$atan",
    "$atan2",
    "$atanh",
    "$ceil",
    "$clog2",
    "$cos",
    "$cosh",
    "$exp",
    "$floor",
    "$hypot",
    "$ln",
    "$log10",
    "$pow",
    "$sin",
    "$sinh",
    "$sqrt",
    "$tan",
    "$tanh",
    # Bit vector system functions (20.9)
    "$countbits",
    "$countones",
    "$isunknown",
    "$onehot",
    "$onehot0",
    # Severity tasks (20.10)
    "$info",
    "$error",
    "$fatal",
    "$warning",
    # Assertion control tasks (20.12)
    "$assertcontrol",
    "$assertfailoff",
    "$assertfailon",
    "$assertkill",
    "$assertnonvacuouson",
    "$assertoff",
    "$asserton",
    "$assertpassoff",
    "$assertpasson",
    "$assertvacuousoff",
    # Sampled value system functions (20.13)
    "$changed",
    "$changed_gclk",
    "$changing_gclk",
    "$falling_gclk",
    "$fell",
    "$fell_gclk",
    "$future_gclk",
    "$past",
    "$past_gclk",
    "$rising_gclk",
    "$rose",
    "$rose_gclk",
    "$sampled",
    "$stable",
    "$stable_gclk",
    "$steady_gclk",
    # Coverage control functions (20.14)
    "$coverage_control",
    "$coverage_get",
    "$coverage_get_max",
    "$coverage_merge",
    "$coverage_save",
    "$get_coverage",
    "$load_coverage_db",
    "$set_coverage_db_name",
    # Probabilistic distribution functions (20.15)
    "$dist_chi_square",
    "$dist_erlang",
    "$dist_exponential",
    "$dist_normal",
    "$dist_poisson",
    "$dist_t",
    "$dist_uniform",
    "$random",
    # Stochastic analysis tasks and functions (20.16)
    "$q_add",
    "$q_exam",
    "$q_full",
    "$q_initialize",
    "$q_remove",
    # PLA modeling tasks (20.17)
    "$async$and$array",
    "$async$and$plane",
    "$async$nand$array",
    "$async$nand$plane",
    "$async$nor$array",
    "$async$nor$plane",
    "$async$or$array",
    "$async$or$plane",
    "$sync$and$array",
    "$sync$and$plane",
    "$sync$nand$array",
    "$sync$nand$plane",
    "$sync$nor$array",
    "$sync$nor$plane",
    "$sync$or$array",
    "$sync$or$plane",
    # Miscellaneous tasks and functions (20.18)
    "$system",
    # Display tasks (21.2)
    "$display",
    "$displayb",
    "$displayh",
    "$displayo",
    "$monitor",
    "$monitorb",
    "$monitorh",
    "$monitoro",
    "$monitoroff",
    "$monitoron",
    "$strobe",
    "$strobeb",
    "$strobeh",
    "$strobeo",
    "$write",
    "$writeb",
    "$writeh",
    "$writeo",
    # File I/O tasks and functions (21.3)
    "$fclose",
    "$fdisplay",
    "$fdisplayb",
    "$fdisplayh",
    "$fdisplayo",
    "$feof",
    "$ferror",
    "$fflush",
    "$fgetc",
    "$fgets",
    "$fmonitor",
    "$fmonitorb",
    "$fmonitorh",
    "$fmonitoro",
    "$fopen",
    "$fread",
    "$fscanf",
    "$fseek",
    "$fstrobe",
    "$fstrobeb",
    "$fstrobeh",
    "$fstrobeo",
    "$ftell",
    "$fwrite",
    "$fwriteb",
    "$fwriteh",
    "$fwriteo",
    "$rewind",
    "$sformat",
    "$sformatf",
    "$sscanf",
    "$swrite",
    "$swriteb",
    "$swriteh",
    "$swriteo",
    "$ungetc",
    # Memory load tasks (21.4)
    "$readmemb",
    "$readmemh",
    # Memory dump tasks (21.5)
    "$writememb",
    "$writememh",
    # Command line input (21.6)
    "$test$plusargs",
    "$value$plusargs",
    # VCD tasks (21.7)
    "$dumpall",
    "$dumpfile",
    "$dumpflush",
    "$dumplimit",
    "$dumpoff",
    "$dumpon",
    "$dumpports",
    "$dumpportsall",
    "$dumpportsflush",
    "$dumpportslimit",
    "$dumpportsoff",
    "$dumpportson",
    "$dumpvars",
)

keywords_tup = (
    "accept_on",
    "alias",
    "always",
    "always_comb",
    "always_ff",
    "always_latch",
    "and",
    "assert",
    "assign",
    "assume",
    "automatic",
    "before",
    "begin",
    "bind",
    "bins",
    "binsof",
    "break",
    "buf",
    "bufif0",
    "bufif1",
    "case",
    "casex",
    "casez",
    "cell",
    "checker",
    "clocking",
    "cmos",
    "config",
    "constraint",
    "context",
    "continue",
    "cover",
    "covergroup",
    "coverpoint",
    "cross",
    "deassign",
    "default",
    "defparam",
    "design",
    "disable",
    "do",
    "edge",
    "else",
    "end",
    "endcase",
    "endchecker",
    "endclocking",
    "endconfig",
    "endfunction",
    "endgenerate",
    "endgroup",
    "endinterface",
    "endmodule",
    "endpackage",
    "endprimitive",
    "endprogram",
    "endproperty",
    "endsequence",
    "endspecify",
    "endtable",
    "endtask",
    "enum",
    "eventually",
    "expect",
    "export",
    "extern",
    "final",
    "first_match",
    "for",
    "force",
    "foreach",
    "forever",
    "fork",
    "forkjoin",
    "function",
    "generate",
    "genvar",
    "global",
    "highz0",
    "highz1",
    "if",
    "iff",
    "ifnone",
    "ignore_bins",
    "illegal_bins",
    "implies",
    "implements",
    "import",
    "incdir",
    "include",
    "initial",
    "inout",
    "input",
    "instance",
    "interconnect",
    "interface",
    "intersect",
    "join",
    "join_any",
    "join_none",
    "large",
    "let",
    "liblist",
    "library",
    "local",
    "localparam",
    "macromodule",
    "matches",
    "medium",
    "modport",
    "module",
    "nand",
    "negedge",
    "nettype",
    "new",
    "nexttime",
    "nmos",
    "nor",
    "noshowcancelled",
    "not",
    "notif0",
    "notif1",
    "null",
    "or",
    "output",
    "package",
    "packed",
    "parameter",
    "pmos",
    "posedge",
    "primitive",
    "priority",
    "program",
    "property",
    "protected",
    "pull0",
    "pull1",
    "pulldown",
    "pullup",
    "pulsestyle_ondetect",
    "pulsestyle_onevent",
    "pure",
    "rand",
    "randc",
    "randcase",
    "randsequence",
    "rcmos",
    "ref",
    "reject_on",
    "release",
    "repeat",
    "restrict",
    "return",
    "rnmos",
    "rpmos",
    "rtran",
    "rtranif0",
    "rtranif1",
    "s_always",
    "s_eventually",
    "s_nexttime",
    "s_until",
    "s_until_with",
    "scalared",
    "sequence",
    "showcancelled",
    "small",
    "soft",
    "solve",
    "specify",
    "specparam",
    "static",
    "strong",
    "strong0",
    "strong1",
    "struct",
    "super",
    "sync_accept_on",
    "sync_reject_on",
    "table",
    "tagged",
    "task",
    "this",
    "throughout",
    "timeprecision",
    "timeunit",
    "tran",
    "tranif0",
    "tranif1",
    "typedef",
    "union",
    "unique",
    "unique0",
    "until",
    "until_with",
    "untyped",
    "use",
    "vectored",
    "virtual",
    "wait",
    "wait_order",
    "weak",
    "weak0",
    "weak1",
    "while",
    "wildcard",
    "with",
    "within",
    "xnor",
    "xor",
)

variable_types_tup = (
    # Variable types
    "bit",
    "byte",
    "chandle",
    "const",
    "event",
    "int",
    "integer",
    "logic",
    "longint",
    "real",
    "realtime",
    "reg",
    "shortint",
    "shortreal",
    "signed",
    "string",
    "time",
    "type",
    "unsigned",
    "var",
    "void",
    # Net types
    "supply0",
    "supply1",
    "tri",
    "triand",
    "trior",
    "trireg",
    "tri0",
    "tri1",
    "uwire",
    "wand",
    "wire",
    "wor",
)

port_types_tup = (
    # Variable types
    "bit",
    "byte",
    "chandle",
    "const",
    "event",
    "int",
    "integer",
    "logic",
    "longint",
    "real",
    "realtime",
    "reg",
    "shortint",
    "shortreal",
    "signed",
    "string",
    "time",
    "type",
    "unsigned",
    "var",
    "void",
    # Net types
    "supply0",
    "supply1",
    "tri",
    "triand",
    "trior",
    "trireg",
    "tri0",
    "tri1",
    "uwire",
    "wand",
    "wire",
    "wor",
)

keywords = (
    words(
        keywords_tup,
        suffix=r"\b",
    ),
    Keyword,
)
variable_types = (
    words(
        variable_types_tup,
        suffix=r"\b",
    ),
    Keyword.Type,
)
builtin = (
    words(
        builtin_tup,
        suffix=r"\b",
    ),
    Name.Builtin,
)
port_types = words(
    port_types_tup,
    suffix=r"\b",
)

keywords_types_tup = keywords_tup + variable_types_tup


def filter_instance_keywords_callback(lexer, match, ctx):  # noqa: ARG001
    """Callback used to filter false matches for the module instances."""
    module_name = match.group(1)
    instance_name = match.group(2)
    connections = match.group(3)

    if instance_name not in keywords_types_tup and module_name not in keywords_types_tup:
        yield match.start(1), Module.Body.Instance.Module, module_name
        yield match.start(2), Module.Body.Instance.Name, instance_name
        ctx.stack.append("instance_connections")
        ctx.pos = match.end(2)
    else:
        yield match.start(1), Error, module_name
        yield match.start(2), Error, instance_name
        yield match.start(3), Error, connections
        ctx.pos = match.end()


def comments_callback(lexer: ExtendedRegexLexer, match, ctx: LexerContext):  # noqa: ARG001
    current_state = ctx.stack[-1]

    # The actual comment is located at group 2
    match_string = match.group(2)
    match_start = match.start(0)

    if current_state == "port_declaration":
        yield match_start, Module.Port.Comment, match_string
    elif current_state == "param_declaration":
        yield match_start, Module.Param.Comment, match_string
    elif current_state == "instance_connections":
        yield match_start, Module.Body.Instance.Con.Comment, match_string
    else:
        yield match_start, Comment, match_string
    ctx.pos = match.end()


class SystemVerilogLexer(ExtendedRegexLexer):
    """Extends verilog lexer to recognise all SystemVerilog keywords.

    SystemVerilog IEEE 1800-2009 standard.
    """

    name = "systemverilog"
    aliases = ["systemverilog", "sv"]
    filenames = ["*.sv", "*.svh"]
    mimetypes = ["text/x-systemverilog"]
    url = "https://en.wikipedia.org/wiki/SystemVerilog"
    version_added = "1.5"
    flags = re.DOTALL

    #: optional Comment or Whitespace
    _ws = r"(?:\s|//.*?\n|/[*].*?[*]/)+"

    tokens = {
        "root": [
            (r"^(\s*)(`define)", bygroups(Whitespace, Comment.Preproc), "macro"),
            (r"^(\s*)(package)(\s+)", bygroups(Whitespace, Keyword.Namespace, Whitespace)),
            (r"^(\s*)(import)(\s+)", bygroups(Whitespace, Keyword.Namespace, Whitespace), "import"),
            (r"\s+", Whitespace),
            (r"(\\)(\n)", bygroups(String.Escape, Whitespace)),  # line continuation
            (r"/(\\\n)?/(\n|(.|\n)*?[^\\]\n)", Comment.Single),
            (r"/(\\\n)?[*](.|\n)*?[*](\\\n)?/", Comment.Multiline),
            (r"[{}#@]", Punctuation),
            (r'L?"', String, "string"),
            (r"L?'(\\.|\\[0-7]{1,3}|\\x[a-fA-F0-9]{1,2}|[^\\\'\n])'", String.Char),
            (r"(\d+\.\d*|\.\d+|\d+)[eE][+-]?\d+[lL]?", Number.Float),
            (r"(\d+\.\d*|\.\d+|\d+[fF])[fF]?", Number.Float),
            (r"([1-9][_0-9]*)?\s*\'[sS]?[bB]\s*[xXzZ?01][_xXzZ?01]*", Number.Bin),
            (r"([1-9][_0-9]*)?\s*\'[sS]?[oO]\s*[xXzZ?0-7][_xXzZ?0-7]*", Number.Oct),
            (r"([1-9][_0-9]*)?\s*\'[sS]?[dD]\s*[xXzZ?0-9][_xXzZ?0-9]*", Number.Integer),
            (r"([1-9][_0-9]*)?\s*\'[sS]?[hH]\s*[xXzZ?0-9a-fA-F][_xXzZ?0-9a-fA-F]*", Number.Hex),
            (r"\'[01xXzZ]", Number),
            (r"[0-9][_0-9]*", Number.Integer),
            (r"[~!%^&*+=|?:<>/-]", Operator),
            (words(("inside", "dist"), suffix=r"\b"), Operator.Word),
            (r"[()\[\],.;\'$]", Punctuation),
            (r"`[a-zA-Z_]\w*", Name.Constant),
            (r"\bmodule\b", Module.ModuleStart, ("module_body", "module_name")),
            keywords,
            builtin,
            (r"(class)(\s+)([a-zA-Z_]\w*)", bygroups(Keyword.Declaration, Whitespace, Name.Class)),
            (r"(extends)(\s+)([a-zA-Z_]\w*)", bygroups(Keyword.Declaration, Whitespace, Name.Class)),
            (
                r"(endclass\b)(?:(\s*)(:)(\s*)([a-zA-Z_]\w*))?",
                bygroups(Keyword.Declaration, Whitespace, Punctuation, Whitespace, Name.Class),
            ),
            variable_types,
            (
                words(
                    (
                        "`__FILE__",
                        "`__LINE__",
                        "`begin_keywords",
                        "`celldefine",
                        "`default_nettype",
                        "`define",
                        "`else",
                        "`elsif",
                        "`end_keywords",
                        "`endcelldefine",
                        "`endif",
                        "`ifdef",
                        "`ifndef",
                        "`include",
                        "`line",
                        "`nounconnected_drive",
                        "`pragma",
                        "`resetall",
                        "`timescale",
                        "`unconnected_drive",
                        "`undef",
                        "`undefineall",
                    ),
                    suffix=r"\b",
                ),
                Comment.Preproc,
            ),
            (r"[a-zA-Z_]\w*:(?!:)", Name.Label),
            (r"\$?[a-zA-Z_]\w*", Name),
            (r"\\(\S+)", Name),
        ],
        "string": [
            (r'"', String, "#pop"),
            (r'\\([\\abfnrtv"\']|x[a-fA-F0-9]{2,4}|[0-7]{1,3})', String.Escape),
            (r'[^\\"\n]+', String),  # all other characters
            (r"(\\)(\n)", bygroups(String.Escape, Whitespace)),  # line continuation
            (r"\\", String),  # stray backslash
        ],
        "macro": [
            (r"[^/\n]+", Comment.Preproc),
            (r"/[*](.|\n)*?[*]/", Comment.Multiline),
            (r"//.*?$", Comment.Single, "#pop"),
            (r"/", Comment.Preproc),
            (r"(?<=\\)\n", Comment.Preproc),
            (r"\n", Whitespace, "#pop"),
        ],
        "import": [(r"[\w:]+\*?", Name.Namespace, "#pop")],
        "module_body": [
            (r"`\w+\s*\(.*?\)", Module.Other),
            (r"\bendmodule\b", Module.ModuleEnd, "#pop"),
            include("comments"),
            include("ifdef"),
            (words(("input", "output", "inout"), prefix=r"\b", suffix=r"\b"), Port.PortDirection, "port_declaration"),
            (r"\bparameter\b", Module.Param, "param_declaration"),
            (r"\bbegin\b", Token.Begin, "begin"),
            keywords,
            builtin,
            preproc,
            (
                r"(\w+)\s*(?:#\(.*?\))?\s+(\w+)\s*\((.*?)\)\s*;",
                filter_instance_keywords_callback,
            ),
            include("root"),
        ],
        "begin": [
            (r"\bend\b", Token.End, "#pop"),
        ],
        "module_name": [
            keywords,  # The keyword module can be followed by the keywords static|automatic
            include("comments"),
            (r"\$?[a-zA-Z_]\w*", Module.ModuleName, ("#pop", "module_header")),
            default("#pop"),
        ],
        "module_header": [
            include("comments"),
            include("ifdef"),
            (r"\bimport\b.*?;", Module.Other),  # Package import declaration
            (r"\bparameter\b", Module.Param, "param_declaration"),  # Parameter declaration
            (
                words(("input", "output", "inout"), prefix=r"\b", suffix=r"\b"),
                Port.PortDirection,
                "port_declaration",
            ),  # Port declaration
            (r";", Module.ModuleHeaderEnd, "#pop"),
            (r"\)\s*;", Module.ModuleHeaderEnd, "#pop"),
            (r"\$?[a-zA-Z_]\w*", Name),
            punctuation,
        ],
        "port_declaration": [
            include("comments"),
            include("ifdef"),
            (words(("signed", "unsigned"), suffix=r"\b", prefix=r"\b"), Port.Dtype),
            (port_types, Port.Ptype),
            # Filter ports used for param declarations
            (r"((\[[^]]+\])+)", Port.PortWidth),  # Match one or more brackets, indicating the port width
            # port declaration ends with a ;, a ); or with the start of another port declaration
            (words(("input", "output", "inout"), suffix=r"\b", prefix=r"\b"), Port.PortDirection),
            (r"\$?[a-zA-Z_]\w*", Port.PortName),
            (r"\)\s*;", Module.HeaderEnd, "#pop:2"),
            (r",", Punctuation),
            (r";", Punctuation, "#pop"),
            default("#pop"),
        ],
        "param_declaration": [
            include("comments"),
            include("ifdef"),
            # Filter macros used for param declarations
            (r"`\w+\s*\(.*?\)", Module.Other),
            (port_types, Module.Param.ParamType),
            # Match one or more brackets, indicating the param width
            (r"((\[[^]]+\])+)", Module.Param.ParamWidth),
            # param declaration ends with a ;, a ); or with the start of another port declaration
            (r"\bparameter\b", Module.Param),
            (r"\blocalparam\b", Keyword, "#pop"),
            (r'=\s*([\d\'hHbBdxXzZ?_][\w\'hHbBdxXzZ]*|"[^"]*")', Punctuation),  # Filter parameter values
            (r"\$?[a-zA-Z_]\w*", Module.Param.ParamName),
            (r"\)\s*;", Module.HeaderEnd, "#pop:2"),
            (r",", Punctuation),
            (r";", Punctuation, "#pop"),
            default("#pop"),
        ],
        "comments": [
            (r"\s+", Whitespace),
            (r"(\\)(\n)", bygroups(String.Escape, Whitespace)),  # line continuation
            (r"/(\\\n)?/(\n|(.|\n)*?[^\\]\n)", comments_callback),
            (r"/(\\\n)?[*]((.|\n)*?)[*](\\\n)?/", comments_callback),
        ],
        "ifdef": [
            (r"(`ifdef)\s+([a-zA-Z_]\w*)", bygroups(Comment.Preproc, Module.IFDEF.IFDEF)),
            (r"(`ifndef)\s+([a-zA-Z_]\w*)", bygroups(Comment.Preproc, Module.IFDEF.IFNDEF)),
            (r"(`else)", Module.IFDEF.ELSE),
            (r"(`elsif)\s+([a-zA-Z_]\w*)", bygroups(Comment.Preproc, Module.IFDEF.ELSIF)),
            (r"(`endif)", Module.IFDEF.ENDIF),
        ],
        "instance_connections": [
            include("comments"),
            # take if-defs into account
            include("ifdef"),
            # Filter macros used for port connections
            (r"`\w+\s*\(.*?\)", Module.Other),
            # autoconnect .*,
            (r"\.[*]\s*,", Module.Body.Instance.Con.Autoconnect),
            # .port(connection),
            (
                r"(\.)([a-zA-Z_]\w*)\s*\(\s*(.*?)\s*\)\s*,?",
                bygroups(
                    Module.Body.Instance.Con.Start, Module.Body.Instance.Con.Port, Module.Body.Instance.Con.Connection
                ),
            ),
            # .port,
            (
                r"(\.)([a-zA-Z_]\w*)\s*,?",
                bygroups(Module.Body.Instance.Con.Start, Module.Body.Instance.Con.PortConnection),
            ),
            # connection by order: (port_a, port_b, port_c);
            (r"([a-zA-Z_]\w*)\s*,?", Module.Body.Instance.Con.OrderedConnection),
            # capture same name connection, example: .clk, .rst_b,
            (r"\s*\(\s*", Punctuation),
            (r"\)\s*;", Punctuation, "#pop"),
        ],
        # "find_connection": [
        #    include("comments"),
        #    (r"\(\s*/\*.*?\*/\s*\)"),
        #    (r"\(\s*/\*.*?\*/\s*\)"),
        #    (r"\.[a-zA-Z_]\w*", Module.Instance.Port, "find_connection"),
        #    (r"\.[a-zA-Z_]\w*,", bygroups(Module.Instance.Port, Module.Instance.PortConnection)),
        #
        # ],
        # "comments": [
        #    (r"\s+", Whitespace),
        #    (r"(\\)(\n)", bygroups(String.Escape, Whitespace)),  # line continuation
        #    (r"/(\\\n)?/(\n|(.|\n)*?[^\\]\n)", Comment.Single),
        #    (r"/(\\\n)?[*](.|\n)*?[*](\\\n)?/", Comment.Multiline),
        #    (r"[{}#@]", Punctuation),
        #    (r'L?"', String, "string"),
        #    (r"L?'(\\.|\\[0-7]{1,3}|\\x[a-fA-F0-9]{1,2}|[^\\\'\n])'", String.Char),
        # ],
    }

    def get_tokens_unprocessed(self, text=None, context=None):  # noqa: C901, PLR0912, PLR0915
        """Split ``text`` into (tokentype, text) pairs.

        If ``context`` is given, use this lexer context instead.
        """
        tokendefs = self._tokens
        if not context:
            ctx = LexerContext(text, 0)
            statetokens = tokendefs["root"]
        else:
            ctx = context
            statetokens = tokendefs[ctx.stack[-1]]
            text = ctx.text
        while 1:
            for rexmatch, action, new_state in statetokens:
                m = rexmatch(text, ctx.pos, ctx.end)
                if m:
                    if action is not None:
                        if type(action) is _TokenType:
                            yield ctx.pos, action, m.group()
                            ctx.pos = m.end()
                        else:
                            yield from action(self, m, ctx)
                            if not new_state:
                                # altered the state stack?
                                statetokens = tokendefs[ctx.stack[-1]]
                    # CAUTION: callback must set ctx.pos!
                    if new_state is not None:
                        LOGGER.debug(f"New State: {new_state}")
                        # state transition
                        if isinstance(new_state, tuple):
                            for state in new_state:
                                if state == "#pop":
                                    if len(ctx.stack) > 1:
                                        ctx.stack.pop()
                                elif state == "#push":
                                    ctx.stack.append(ctx.stack[-1])
                                else:
                                    ctx.stack.append(state)
                        elif isinstance(new_state, int):
                            # see RegexLexer for why this check is made
                            if abs(new_state) >= len(ctx.stack):
                                del ctx.stack[1:]
                            else:
                                del ctx.stack[new_state:]
                        elif new_state == "#push":
                            ctx.stack.append(ctx.stack[-1])
                        else:
                            raise RuntimeError(f"wrong state def: {new_state!r}")
                        statetokens = tokendefs[ctx.stack[-1]]
                    break
            else:
                try:
                    if ctx.pos >= ctx.end:
                        break
                    if text[ctx.pos] == "\n":
                        # at EOL, reset state to "root"
                        ctx.stack = ["root"]
                        statetokens = tokendefs["root"]
                        yield ctx.pos, Text, "\n"
                        ctx.pos += 1
                        continue
                    yield ctx.pos, Error, text[ctx.pos]
                    ctx.pos += 1
                except IndexError:
                    break
