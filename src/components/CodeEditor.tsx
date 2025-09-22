import React from 'react';
import Editor from '@monaco-editor/react';

interface CodeEditorProps {
  value: string;
  onChange?: (value: string) => void;
  language?: string;
  height?: string;
  readOnly?: boolean;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ 
  value, 
  onChange, 
  language = 'python',
  height = '300px',
  readOnly = false
}) => {
  const handleEditorChange = (val: string | undefined) => {
    if (onChange) {
      onChange(val || '');
    }
  };

  return (
    <div className="border border-gray-300 rounded-md overflow-hidden">
      <Editor
        height={height}
        language={language}
        value={value}
        onChange={handleEditorChange}
        theme="vs-light"
        options={{
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 14,
          lineNumbers: 'on',
          roundedSelection: false,
          automaticLayout: true,
          wordWrap: 'on',
          folding: false,
          readOnly: readOnly,
          contextmenu: false,
          selectOnLineNumbers: false,
          cursorBlinking: readOnly ? 'solid' : 'blink',
          cursorStyle: readOnly ? 'line-thin' : 'line',
          cursorWidth: readOnly ? 0 : 2,
          hideCursorInOverviewRuler: readOnly,
          overviewRulerBorder: false,
          scrollbar: {
            alwaysConsumeMouseWheel: false
          },
          mouseWheelZoom: false,
          selectionHighlight: !readOnly,
          occurrencesHighlight: readOnly ? 'off' : 'singleFile',
          renderLineHighlight: readOnly ? 'none' : 'line',
          quickSuggestions: !readOnly,
          parameterHints: {
            enabled: !readOnly
          },
          suggestOnTriggerCharacters: !readOnly,
          acceptSuggestionOnEnter: readOnly ? 'off' : 'on',
          tabCompletion: readOnly ? 'off' : 'on',
          snippetSuggestions: readOnly ? 'none' : 'inline',
          domReadOnly: readOnly,
        }}
      />
    </div>
  );
};

export default CodeEditor;