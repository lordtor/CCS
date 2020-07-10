define(["require", "exports", "../_.contribution"], function (require, exports, __contribution_1) {
    /*---------------------------------------------------------------------------------------------
     *  Copyright (c) Microsoft Corporation. All rights reserved.
     *  Licensed under the MIT License. See License.txt in the project root for license information.
     *--------------------------------------------------------------------------------------------*/
    'use strict';
    Object.defineProperty(exports, "__esModule", { value: true });
    __contribution_1.registerLanguage({
        id: 'dart',
        extensions: ['.dart'],
        aliases: ['Dart', 'dart'],
        mimetypes: ['text/x-dart-source', 'text/x-dart'],
        loader: function () { return new Promise(function (resolve_1, reject_1) { require(['./dart'], resolve_1, reject_1); }); }
    });
});
