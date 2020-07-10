/// <reference path="../vendor/monaco-editor/monaco.d.ts" />
'use strict';
require.config({
    baseUrl: ""
});


var editor = null,
    diffEditor = null;

$(document).ready(function() {
    require(['vs/editor/editor.main'], function() {
        var MODES = (function() {
            var modesIds = monaco.languages.getLanguages().map(function(lang) {return lang.id; });
            modesIds.sort();

            return modesIds.map(function(modeId) {
                return {
                    modeId: modeId,
                    sampleURL: 'https://microsoft.github.io/monaco-editor/index/samples/sample.' + modeId + '.txt'
                };
            });
        })();
        var startModeIndex = 0;
        for (var i = 0; i < MODES.length; i++) {
            var o = document.createElement('option');
            o.textContent = MODES[i].modeId;
            $(".language-picker").append(o);
        }
        $(".language-picker")[0].selectedIndex = startModeIndex;
        loadSample(MODES[startModeIndex]);
        $(".language-picker").change(function() {
          loadSample(MODES[this.selectedIndex]);
        });

        $(".theme-picker").change(function() {
          changeTheme(this.selectedIndex);
        });

    });

    window.onresize = function() {
        if (editor) {
            editor.layout();
        }
    };
});


function loadSample(mode) {
    $.ajax({
        type: 'GET',
        url: mode.sampleURL,
        dataType: 'text',
        beforeSend: function() {
            $('.loading.editor').show();
        },
        error: function() {
            if (editor) {
                if (editor.getModel()) {
                    editor.getModel().dispose();
                }
                editor.dispose();
                editor = null;
            }
            $('.loading.editor').fadeOut({
                duration: 200
            });
            $('#editor').empty();
            $('#editor').append('<p class="alert alert-error">Failed to load ' + mode.modeId + ' sample</p>');
        }
    }).done(function(data) {
        if (!editor) {
            $('#editor').empty();
            editor = monaco.editor.create(document.getElementById('editor'), {
                model: null,
            });
        }
        
        var oldModel = editor.getModel();
        var newModel = monaco.editor.createModel(t, mode.modeId);
        editor.setModel(newModel);
        if (oldModel) {
            oldModel.dispose();
        }
        $('.loading.editor').fadeOut({
            duration: 300
        });
    });
}

function changeTheme(theme) {
	var newTheme = (theme === 1 ? 'vs-dark' : ( theme === 0 ? 'vs' : 'hc-black' ));
	monaco.editor.setTheme(newTheme);
}
