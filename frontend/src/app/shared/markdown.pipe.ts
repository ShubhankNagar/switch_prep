import { Pipe, PipeTransform } from '@angular/core';
import { Marked } from 'marked';
import hljs from 'highlight.js/lib/core';
import java from 'highlight.js/lib/languages/java';
import python from 'highlight.js/lib/languages/python';
import sql from 'highlight.js/lib/languages/sql';
import typescript from 'highlight.js/lib/languages/typescript';
import javascript from 'highlight.js/lib/languages/javascript';
import bash from 'highlight.js/lib/languages/bash';
import json from 'highlight.js/lib/languages/json';
import yaml from 'highlight.js/lib/languages/yaml';
import xml from 'highlight.js/lib/languages/xml';

hljs.registerLanguage('java', java);
hljs.registerLanguage('python', python);
hljs.registerLanguage('sql', sql);
hljs.registerLanguage('typescript', typescript);
hljs.registerLanguage('ts', typescript);
hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('js', javascript);
hljs.registerLanguage('bash', bash);
hljs.registerLanguage('shell', bash);
hljs.registerLanguage('json', json);
hljs.registerLanguage('yaml', yaml);
hljs.registerLanguage('xml', xml);
hljs.registerLanguage('html', xml);

const escapeHtml = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const marked = new Marked({
  gfm: true,
  breaks: false,
  renderer: {
    code({ text, lang }) {
      const language = (lang ?? '').trim().split(/\s/)[0];
      const body = language && hljs.getLanguage(language)
        ? hljs.highlight(text, { language }).value
        : escapeHtml(text);
      return `<pre class="code"><code class="hljs">${body}</code></pre>`;
    },
    link({ href, text }) {
      return `<a href="${href}" target="_blank" rel="noopener">${text}</a>`;
    },
  },
});

/** Renders markdown (with syntax-highlighted code blocks) to HTML. Angular sanitizes the result. */
@Pipe({ name: 'md' })
export class MarkdownPipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    return value ? (marked.parse(value) as string) : '';
  }
}

/** Highlights a raw code string (used for solutions stored without markdown fences). */
@Pipe({ name: 'code' })
export class CodePipe implements PipeTransform {
  transform(value: string | null | undefined, language = 'java'): string {
    if (!value) return '';
    const v = value.trim();
    if (v.startsWith('```')) return marked.parse(v) as string;
    // Some final-round solutions are SQL queries rather than Java.
    if (/^(--|select\b|with\b)/i.test(v)) language = 'sql';
    const body = hljs.getLanguage(language) ? hljs.highlight(v, { language }).value : escapeHtml(v);
    return `<pre class="code"><code class="hljs">${body}</code></pre>`;
  }
}
