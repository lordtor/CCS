/// <reference path="../vendor/monaco-editor/monaco.d.ts" />

class MonacoEditor extends HTMLElement {
    // attributeChangedCallback will be called when the value of one of these attributes is changed in html
    static get observedAttributes() {
        return ['value', 'language'];
    }

    private editor: monaco.editor.IStandaloneCodeEditor | null = null;
    private _form: HTMLFormElement | null = null;

    constructor() {
        super();

        // keep reference to <form> for cleanup
        this._form = null;
        this._handleFormData = this._handleFormData.bind(this);
    }

    attributeChangedCallback(name: string, oldValue: any, newValue: any) {
        if (this.editor) {
            if (name === 'value') {
                this.editor.setValue(newValue);
            }

            if (name === 'language') {
                const currentModel = this.editor.getModel();
                if (currentModel) {
                    currentModel.dispose();
                }

                this.editor.setModel(monaco.editor.createModel(this._getEditorValue(), newValue));
            }
        }
    }

    connectedCallback() {
        this._form = this._findContainingForm();
        if (this._form) {
            this._form.addEventListener('formdata', this._handleFormData);
        }

        // editor
        const editor = document.createElement('div');
        editor.style.minHeight = '200px';
        editor.style.maxHeight = '100vh';
        editor.style.height = '100%';
        editor.style.width = '100%';
        editor.style.resize = 'vertical';
        editor.style.overflow = 'auto';

        this.appendChild(editor);

        // window.editor is accessible.
        var init = () => {
            require(['vs/editor/editor.main'], () => {
                console.log(monaco.languages.getLanguages().map(lang => lang.id));

                // Editor
                this.editor = monaco.editor.create(editor, {
                    theme: 'vs-dark',
                    model: monaco.editor.createModel(this.getAttribute("value"), this.getAttribute("language")),
                    wordWrap: 'on',
                    automaticLayout: true,
                    minimap: {
                        enabled: false
                    },
                    scrollbar: {
                        vertical: 'auto'
                    }
                });
            });

            window.removeEventListener("load", init);
        };

        window.addEventListener("load", init);
    }

    disconnectedCallback() {
        if (this._form) {
            this._form.removeEventListener('formdata', this._handleFormData);
            this._form = null;
        }
    }

    private _getEditorValue() {
        if (this.editor) {
            return this.editor.getModel().getValue();
        }

        return null;
    }

    private _handleFormData(ev: FormDataEvent) {
        ev.formData.append(this.getAttribute('name'), this._getEditorValue());
    }

    private _findContainingForm(): HTMLFormElement | null {
        // can only be in a form in the same "scope", ShadowRoot or Document
        const root = this.getRootNode();
        if (root instanceof Document || root instanceof Element) {
            const forms = Array.from(root.querySelectorAll('form'));
            // we can only be in one <form>, so the first one to contain us is the correct one
            return forms.find((form) => form.contains(this)) || null;
        }

        return null;
    }
}

customElements.define('monaco-editor', MonacoEditor);

interface FormDataEvent extends Event {
    readonly formData: FormData;
};

declare function require(files: string[], onLoaded: () => void): void;