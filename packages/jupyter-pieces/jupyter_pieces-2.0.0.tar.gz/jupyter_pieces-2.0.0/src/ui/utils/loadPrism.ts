import * as Prism from 'prismjs';
import 'prismjs/components/prism-batch';
import 'prismjs/components/prism-coffeescript';
import 'prismjs/components/prism-erlang';
import 'prismjs/components/prism-haskell';
import 'prismjs/components/prism-lua';
import 'prismjs/components/prism-markdown';
import 'prismjs/components/prism-matlab';
import 'prismjs/components/prism-c';
import 'prismjs/components/prism-cpp';
import 'prismjs/components/prism-csharp';
import 'prismjs/components/prism-css';
import 'prismjs/components/prism-go';
import 'prismjs/components/prism-cshtml';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-dart';
import 'prismjs/components/prism-scala';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-perl';
// import 'prismjs/components/prism-php'; // Breaks
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-powershell';
import 'prismjs/components/prism-r';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-swift';
import 'prismjs/components/prism-ruby';
import 'prismjs/components/prism-latex';
import 'prismjs/components/prism-textile';
import 'prismjs/components/prism-rust';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-yaml';
import 'prismjs/components/prism-toml';
// import 'prismjs/components/prism-xml-doc'; // Breaks
import 'prismjs/components/prism-groovy';
import 'prismjs/components/prism-kotlin';
import 'prismjs/components/prism-clojure';
import 'prismjs/components/prism-lisp';
import 'prismjs/components/prism-elixir';

Prism.languages.batch = Prism.languages.extend('batch', {});
Prism.languages.coffeescript = Prism.languages.extend('coffeescript', {});
Prism.languages.erlang = Prism.languages.extend('erlang', {});
Prism.languages.haskell = Prism.languages.extend('haskell', {});
Prism.languages.lua = Prism.languages.extend('lua', {});
Prism.languages.markdown = Prism.languages.extend('markdown', {});
Prism.languages.matlab = Prism.languages.extend('matlab', {});
Prism.languages.c = Prism.languages.extend('c', {});
Prism.languages.cpp = Prism.languages.extend('cpp', {});
Prism.languages.csharp = Prism.languages.extend('csharp', {});
Prism.languages.css = Prism.languages.extend('css', {});
Prism.languages.go = Prism.languages.extend('go', {});
Prism.languages.cshtml = Prism.languages.extend('cshtml', {});
Prism.languages.java = Prism.languages.extend('java', {});
Prism.languages.javascript = Prism.languages.extend('javascript', {});
Prism.languages.typescript = Prism.languages.extend('typescript', {});
Prism.languages.dart = Prism.languages.extend('dart', {});
Prism.languages.scala = Prism.languages.extend('scala', {});
Prism.languages.sql = Prism.languages.extend('sql', {});
Prism.languages.perl = Prism.languages.extend('perl', {});
Prism.languages.python = Prism.languages.extend('python', {});
Prism.languages.powershell = Prism.languages.extend('powershell', {});
Prism.languages.r = Prism.languages.extend('r', {});
Prism.languages.bash = Prism.languages.extend('bash', {});
Prism.languages.swift = Prism.languages.extend('swift', {});
Prism.languages.ruby = Prism.languages.extend('ruby', {});
Prism.languages.latex = Prism.languages.extend('latex', {});
Prism.languages.textile = Prism.languages.extend('textile', {});
Prism.languages.rust = Prism.languages.extend('rust', {});
Prism.languages.json = Prism.languages.extend('json', {});
Prism.languages.yaml = Prism.languages.extend('yaml', {});
Prism.languages.toml = Prism.languages.extend('toml', {});
// Prism.languages['xml-doc'] = Prism.languages.extend('xml-doc', {});
Prism.languages.groovy = Prism.languages.extend('groovy', {});
Prism.languages.kotlin = Prism.languages.extend('kotlin', {});
Prism.languages.clojure = Prism.languages.extend('clojure', {});
Prism.languages.lisp = Prism.languages.extend('lisp', {});
Prism.languages.elixir = Prism.languages.extend('elixir', {});

export const highlightSnippet = ({
  snippetContent,
  snippetLanguage,
}: {
  snippetContent: string;
  snippetLanguage: string;
}): string => {
  snippetLanguage = snippetLanguage?.toLowerCase() ?? 'py';
  switch (snippetLanguage) {
    case 'bat':
      return Prism.highlight(snippetContent, Prism.languages.batch, 'batch');
      break;
    case 'coffee':
      return Prism.highlight(
        snippetContent,
        Prism.languages.coffeescript,
        'coffeescript'
      );
      break;
    case 'erl':
      return Prism.highlight(snippetContent, Prism.languages.erlang, 'erlang');
      break;
    case 'hs':
      return Prism.highlight(
        snippetContent,
        Prism.languages.haskell,
        'haskell'
      );
      break;
    case 'lua':
      return Prism.highlight(snippetContent, Prism.languages.lua, 'lua');
      break;
    case 'md':
      return Prism.highlight(
        snippetContent,
        Prism.languages.markdown,
        'markdown'
      );
      break;
    case 'matlab':
      return Prism.highlight(snippetContent, Prism.languages.matlab, 'matlab');
      break;
    case 'm':
      return Prism.highlight(snippetContent, Prism.languages.cpp, 'cpp');
      break;
    case 'c':
      return Prism.highlight(snippetContent, Prism.languages.c, 'c');
      break;
    case 'cc':
    case 'h':
    case 'hh':
    case 'cpp':
      return Prism.highlight(snippetContent, Prism.languages.cpp, 'cpp');
      break;
    case 'cs':
      return Prism.highlight(snippetContent, Prism.languages.csharp, 'csharp');
      break;
    case 'css':
      return Prism.highlight(snippetContent, Prism.languages.css, 'css');
      break;
    case 'go':
      return Prism.highlight(snippetContent, Prism.languages.go, 'go');
      break;
    case 'htm':
    case 'html':
      return Prism.highlight(snippetContent, Prism.languages.html, 'html');
      break;
    case 'java':
      return Prism.highlight(snippetContent, Prism.languages.java, 'java');
      break;
    case 'js':
      return Prism.highlight(
        snippetContent,
        Prism.languages.javascript,
        'javascript'
      );
      break;
    case 'ts':
      return Prism.highlight(
        snippetContent,
        Prism.languages.typescript,
        'typescript'
      );
      break;
    case 'dart':
      return Prism.highlight(snippetContent, Prism.languages.dart, 'dart');
      break;
    case 'scala':
      return Prism.highlight(snippetContent, Prism.languages.scala, 'scala');
      break;
    case 'sql':
      return Prism.highlight(snippetContent, Prism.languages.sql, 'sql');
      break;
    case 'pl':
      return Prism.highlight(snippetContent, Prism.languages.perl, 'perl');
      break;
    case 'pyc':
    case 'py':
      return Prism.highlight(snippetContent, Prism.languages.python, 'python');
      break;
    case 'ps1':
      return Prism.highlight(
        snippetContent,
        Prism.languages.powershell,
        'powershell'
      );
      break;
    case 'r':
      return Prism.highlight(snippetContent, Prism.languages.r, 'r');
      break;
    case 'sh':
      return Prism.highlight(snippetContent, Prism.languages.bash, 'bash');
      break;
    case 'swift':
      return Prism.highlight(snippetContent, Prism.languages.swift, 'swift');
      break;
    case 'rb':
      return Prism.highlight(snippetContent, Prism.languages.ruby, 'ruby');
      break;
    case 'tex':
      return Prism.highlight(snippetContent, Prism.languages.latex, 'latex');
      break;
    case 'text':
    case 'txt':
      return snippetContent;
      break;
    case 'rs':
      return Prism.highlight(snippetContent, Prism.languages.rust, 'rust');
      break;
    case 'json':
      return Prism.highlight(snippetContent, Prism.languages.json, 'json');
      break;
    case 'yaml':
    case 'yml':
      return Prism.highlight(snippetContent, Prism.languages.yaml, 'yaml');
      break;
    case 'toml':
      return Prism.highlight(snippetContent, Prism.languages.toml, 'toml');
      break;
    case 'xml':
      return Prism.highlight(snippetContent, Prism.languages.xml, 'xml');
      break;
    case 'groovy':
      return Prism.highlight(snippetContent, Prism.languages.groovy, 'groovy');
      break;
    case 'kt':
      return Prism.highlight(snippetContent, Prism.languages.kotlin, 'kotlin');
      break;
    case 'clj':
      return Prism.highlight(
        snippetContent,
        Prism.languages.clojure,
        'clojure'
      );
      break;
    case 'el':
      return Prism.highlight(snippetContent, Prism.languages.lisp, 'lisp');
      break;
    case 'ex':
      return Prism.highlight(snippetContent, Prism.languages.elixir, 'elixir');
      break;
    default:
      return snippetContent;
      break;
  }
};

export default Prism;
