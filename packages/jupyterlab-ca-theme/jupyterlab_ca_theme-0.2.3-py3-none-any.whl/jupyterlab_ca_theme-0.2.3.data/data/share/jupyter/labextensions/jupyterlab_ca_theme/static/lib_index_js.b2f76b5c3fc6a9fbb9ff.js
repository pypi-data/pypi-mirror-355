"use strict";
(self["webpackChunkjupyterlab_ca_theme"] = self["webpackChunkjupyterlab_ca_theme"] || []).push([["lib_index_js"],{

/***/ "./lib/index.js":
/*!**********************!*\
  !*** ./lib/index.js ***!
  \**********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @jupyterlab/apputils */ "webpack/sharing/consume/default/@jupyterlab/apputils");
/* harmony import */ var _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _lumino_disposable__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @lumino/disposable */ "webpack/sharing/consume/default/@lumino/disposable");
/* harmony import */ var _lumino_disposable__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_lumino_disposable__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _style_index_css__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../style/index.css */ "./style/index.css");




var CommandIDs;
(function (CommandIDs) {
    CommandIDs.changeTheme = 'apputils:change-theme';
    CommandIDs.loadState = 'apputils:load-statedb';
    CommandIDs.recoverState = 'apputils:recover-statedb';
    CommandIDs.reset = 'apputils:reset';
    CommandIDs.resetOnLoad = 'apputils:reset-on-load';
    CommandIDs.saveState = 'apputils:save-statedb';
})(CommandIDs || (CommandIDs = {}));
/**
 * Initialization data for the jupyterlab_ca_theme extension.
 */
const plugin = {
    id: 'jupyterlab_ca_theme:plugin',
    description: 'A JupyterLab extension theme for Composable Analytics DataLabs.',
    autoStart: true,
    requires: [_jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.IThemeManager],
    activate: (app, manager) => {
        console.log('JupyterLab extension jupyterlab_ca_theme is activated!');
        const style = 'jupyterlab_ca_theme/index.css';
        manager.register({
            name: 'jupyterlab_ca_theme',
            isLight: true,
            load: () => manager.loadCSS(style),
            unload: () => Promise.resolve(undefined)
        });
    }
};
const splash = {
    id: '@jupyterlab/mysplash:splash',
    autoStart: true,
    provides: _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.ISplashScreen,
    activate: (app) => {
        return {
            show: (light = true) => {
                const { commands, restored } = app;
                return Private.showSplash(restored, commands, CommandIDs.reset, light);
            }
        };
    }
};
var Private;
(function (Private) {
    /**
     * Create a splash element.
     */
    function createSplash() {
        const splash = document.createElement('div');
        splash.classList.add('loading-overlay');
        const loadingSVG = document.createElement('div');
        loadingSVG.classList.add('loading-svg');
        const svg = document.createElementNS('http://www.w3.org/2000/svg', "svg");
        svg.id = 'layer1';
        svg.setAttribute('x', '0px');
        svg.setAttribute('y', '0px');
        svg.setAttribute('viewBox', '0 0 219.9 265.9');
        svg.setAttribute('xml:space', 'preserve');
        const styleTag = document.createElement('style');
        styleTag.setAttribute('type', 'text/css');
        styleTag.innerHTML = `.pol2.st0{fill:none;stroke:#d2d6de;stroke-miterlimit:10; stroke-width: 3}
                            .pol1.st0{fill:none;stroke:#0c4e7d;stroke-miterlimit:10; stroke-width: 4}`;
        svg.appendChild(styleTag);
        const g1 = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        const polygon1 = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon1.setAttribute('class', 'pol2 st0');
        polygon1.setAttribute('points', '0.5,177.5 0.5,71.5 119,0.9 119,106.9 77.3,131.7');
        g1.appendChild(polygon1);
        const polyline1 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        polyline1.setAttribute('class', 'pol2 st0');
        polyline1.setAttribute('points', '77.3,131.7 77.3,226 0.5,177.5');
        g1.appendChild(polyline1);
        svg.appendChild(g1);
        const g2 = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        const polygon2 = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon2.setAttribute('class', 'pol2 st0');
        polygon2.setAttribute('points', '219.3,88.4 219.3,194.4 100.8,265 100.8,159 142.4,134.1');
        g2.appendChild(polygon2);
        const polyline2 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        polyline2.setAttribute('class', 'pol2 st0');
        polyline2.setAttribute('points', '142.4,134.1 142.4,39.9 219.3,88.4');
        g2.appendChild(polyline2);
        svg.appendChild(g2);
        const g3 = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        const polygon3 = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon3.setAttribute('class', 'pol1 st0');
        polygon3.setAttribute('points', '0.5,177.5 0.5,71.5 119,0.9 119,106.9 77.3,131.7');
        g3.appendChild(polygon3);
        const polyline3 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        polyline3.setAttribute('class', 'pol1 st0');
        polyline3.setAttribute('points', '77.3,131.7 77.3,226 0.5,177.5');
        g3.appendChild(polyline3);
        svg.appendChild(g3);
        const g4 = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        const polygon4 = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon4.setAttribute('class', 'pol1 st0');
        polygon4.setAttribute('points', '219.3,88.4 219.3,194.4 100.8,265 100.8,159 142.4,134.1');
        g4.appendChild(polygon4);
        const polyline4 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
        polyline4.setAttribute('class', 'pol1 st0');
        polyline4.setAttribute('points', '142.4,134.1 142.4,39.9 219.3,88.4');
        g4.appendChild(polyline4);
        svg.appendChild(g4);
        loadingSVG.appendChild(svg);
        let leftLine1 = document.createElement("div");
        let leftLine2 = document.createElement("div");
        let leftLine3 = document.createElement("div");
        let leftLine4 = document.createElement("div");
        let leftLine5Wrap = document.createElement("div");
        let leftLine5 = document.createElement("div");
        let leftLine6 = document.createElement("div");
        leftLine1.setAttribute('class', 'line left-line-1');
        leftLine2.setAttribute('class', 'line left-line-2');
        leftLine3.setAttribute('class', 'line left-line-3');
        leftLine4.setAttribute('class', 'line left-line-4');
        leftLine5Wrap.setAttribute('class', 'line left-line-5-wrap');
        leftLine5.setAttribute('class', 'line left-line-5');
        leftLine6.setAttribute('class', 'line left-line-6');
        leftLine5Wrap.appendChild(leftLine5);
        loadingSVG.appendChild(leftLine1);
        loadingSVG.appendChild(leftLine2);
        loadingSVG.appendChild(leftLine3);
        loadingSVG.appendChild(leftLine4);
        loadingSVG.appendChild(leftLine5Wrap);
        loadingSVG.appendChild(leftLine6);
        let rightLine1 = document.createElement("div");
        let rightLine2 = document.createElement("div");
        let rightLine3 = document.createElement("div");
        let rightLine4 = document.createElement("div");
        let rightLine5Wrap = document.createElement("div");
        let rightLine5 = document.createElement("div");
        let rightLine6 = document.createElement("div");
        rightLine1.setAttribute('class', 'line right-line-1');
        rightLine2.setAttribute('class', 'line right-line-2');
        rightLine3.setAttribute('class', 'line right-line-3');
        rightLine4.setAttribute('class', 'line right-line-4');
        rightLine5Wrap.setAttribute('class', 'line right-line-5-wrap');
        rightLine5.setAttribute('class', 'line right-line-5');
        rightLine6.setAttribute('class', 'line right-line-6');
        rightLine5Wrap.appendChild(rightLine5);
        loadingSVG.appendChild(rightLine1);
        loadingSVG.appendChild(rightLine2);
        loadingSVG.appendChild(rightLine3);
        loadingSVG.appendChild(rightLine4);
        loadingSVG.appendChild(rightLine5Wrap);
        loadingSVG.appendChild(rightLine6);
        splash.appendChild(loadingSVG);
        return splash;
    }
    /**
     * A debouncer for recovery attempts.
     */
    let debouncer = 0;
    /**
     * The recovery dialog.
     */
    let dialog;
    /**
     * Allows the user to clear state if splash screen takes too long.
     */
    function recover(fn) {
        if (dialog) {
            return;
        }
        dialog = new _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog({
            title: 'Loading...',
            body: `The loading screen is taking a long time.
      Would you like to clear the workspace or keep waiting?`,
            buttons: [
                _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog.cancelButton({ label: 'Keep Waiting' }),
                _jupyterlab_apputils__WEBPACK_IMPORTED_MODULE_0__.Dialog.warnButton({ label: 'Clear Workspace' })
            ]
        });
        dialog
            .launch()
            .then(result => {
            if (result.button.accept) {
                return fn();
            }
            dialog.dispose();
            //dialog = null;
            debouncer = window.setTimeout(() => {
                recover(fn);
            }, 700);
        })
            .catch(() => {
            /* no-op */
        });
    }
    /**
     * The splash element.
     */
    const splash = createSplash();
    /**
     * The splash screen counter.
     */
    let splashCount = 0;
    /**
     * Show the splash element.
     *
     * @param ready - A promise that must be resolved before splash disappears.
     *
     * @param recovery - A command that recovers from a hanging splash.
     */
    function showSplash(ready, commands, recovery, light) {
        splash.classList.remove('splash-fade');
        splash.classList.toggle('light', light);
        splash.classList.toggle('dark', !light);
        splashCount++;
        if (debouncer) {
            window.clearTimeout(debouncer);
        }
        debouncer = window.setTimeout(() => {
            if (commands.hasCommand(recovery)) {
                recover(() => {
                    commands.execute(recovery, {});
                });
            }
        }, 7000);
        document.body.appendChild(splash);
        return new _lumino_disposable__WEBPACK_IMPORTED_MODULE_1__.DisposableDelegate(() => {
            ready.then(() => {
                if (--splashCount === 0) {
                    if (debouncer) {
                        window.clearTimeout(debouncer);
                        debouncer = 0;
                    }
                    if (dialog) {
                        dialog.dispose();
                        //dialog = null;
                    }
                    splash.classList.add('splash-fade');
                    window.setTimeout(() => {
                        document.body.removeChild(splash);
                    }, 500);
                }
            });
        });
    }
    Private.showSplash = showSplash;
})(Private || (Private = {}));
const plugins = [
    plugin,
    splash
];
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (plugins);


/***/ }),

/***/ "./node_modules/css-loader/dist/cjs.js!./style/index.css":
/*!***************************************************************!*\
  !*** ./node_modules/css-loader/dist/cjs.js!./style/index.css ***!
  \***************************************************************/
/***/ ((module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _node_modules_css_loader_dist_runtime_sourceMaps_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../node_modules/css-loader/dist/runtime/sourceMaps.js */ "./node_modules/css-loader/dist/runtime/sourceMaps.js");
/* harmony import */ var _node_modules_css_loader_dist_runtime_sourceMaps_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_node_modules_css_loader_dist_runtime_sourceMaps_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../node_modules/css-loader/dist/runtime/api.js */ "./node_modules/css-loader/dist/runtime/api.js");
/* harmony import */ var _node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _node_modules_css_loader_dist_cjs_js_variables_css__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! -!../node_modules/css-loader/dist/cjs.js!./variables.css */ "./node_modules/css-loader/dist/cjs.js!./style/variables.css");
// Imports



var ___CSS_LOADER_EXPORT___ = _node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1___default()((_node_modules_css_loader_dist_runtime_sourceMaps_js__WEBPACK_IMPORTED_MODULE_0___default()));
___CSS_LOADER_EXPORT___.i(_node_modules_css_loader_dist_cjs_js_variables_css__WEBPACK_IMPORTED_MODULE_2__["default"]);
// Module
___CSS_LOADER_EXPORT___.push([module.id, `/*-----------------------------------------------------------------------------
| Copyright (c) Jupyter Development Team.
| Distributed under the terms of the Modified BSD License.
|----------------------------------------------------------------------------*/

/* Set the default typography for monospace elements */
tt,
code,
kbd,
samp,
pre {
  font-family: var(--jp-code-font-family);
  font-size: var(--jp-code-font-size);
  line-height: var(--jp-code-line-height);
}

/* Top menubar styles */
#jp-top-panel {
    border-bottom: 0;
    background: var(--jp-layout-color2);
}

#jp-menu-panel {
    background: var(--jp-layout-color2);
}

.lm-MenuBar {
    background: var(--jp-layout-color2);
}

.lm-MenuBar-item.lm-mod-active {
    background: var(--jp-layout-color4);
}

/* Left expanded sidebar */
#jp-left-stack {
    border-right: 2px solid var(--jp-layout-color3);
}

/* Left sidebar styles */
.jp-SideBar.lm-TabBar.jp-mod-left {
    border: 0;
}

.jp-SideBar .lm-TabBar-tab {
    border: none;
    border-image: none;
}

.jp-SideBar .lm-TabBar-tab.lm-mod-current {
    border: none;
}

/* Right sidebar */
.jp-SideBar.lm-TabBar.jp-mod-right {
    border: 0;
}

/* Button dialog style */
button.jp-mod-styled.jp-mod-accept {
    background-color: #3c8dbc;
}

/* Loading animation */

.splash-fade {
    animation: 0.5s fade-out forwards;
}

.loading-overlay {
    z-index: 2000;
    border: none;
    margin: 0px;
    padding: 0px;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    background-color: white;
    opacity: 0.9;
    position: fixed;
    text-align: center;
}

    .loading-overlay svg {
        height: 150px;
        width: 150px;
    }

    .loading-overlay .loading-svg {
        width: 150px;
        height: 150px;
        position: absolute;
        top: calc(50% - 65px);
        left: calc(50% - 75px);
    }

    .loading-overlay .line {
        width: 5px;
        height: 200px;
        position: absolute;
        animation-delay: 1000ms;
        background-color: white;
    }

    .loading-overlay .left-line-1,
    .loading-overlay .right-line-1 {
        left: 50%;
        height: 81px;
    }

    .loading-overlay .left-line-1 {
        transform: rotate(59deg) translateX(-199px) translateY(-42px) scaleY(0);
        transform-origin: 50% 100%;
        animation: left-line1 6000ms linear infinite;
        animation-fill-mode: forwards;
    }

    .loading-overlay .right-line-1 {
        transform: rotate(59deg) translateX(-7px) translateY(-75px) scaleY(0);
        transform-origin: 50% 0%;
        animation: right-line1 6000ms linear infinite;
        animation-fill-mode: forwards;
    }

    .loading-overlay .left-line-2,
    .loading-overlay .right-line-2 {
        left: 50%;
        height: 64px;
    }

    .loading-overlay .left-line-2 {
        transform: translateY(-154px) translateX(2px) scaleY(0);
        transform-origin: 50% 0%;
        animation: left-line2 6000ms linear infinite;
        animation-fill-mode: forwards;
    }

    .loading-overlay .right-line-2 {
        transform: translateY(-68px) translateX(-7px) scaleY(0);
        transform-origin: 50% 100%;
        animation: right-line2 6000ms linear infinite;
        animation-fill-mode: forwards;
    }

    .loading-overlay .left-line-3,
    .loading-overlay .right-line-3 {
        left: 50%;
        height: 76px;
    }

    .loading-overlay .left-line-3 {
        transform: rotate(59deg) translateX(-79px) translateY(-51px) scaleY(0);
        transform-origin: 50% 0%;
        animation: left-line3 6000ms linear infinite;
        animation-fill-mode: forwards;
    }

    .loading-overlay .right-line-3 {
        transform: rotate(59deg) translateX(-125px) translateY(-67px) scaleY(0);
        transform-origin: 50% 100%;
        animation: right-line3 6000ms linear infinite;
        animation-fill-mode: forwards;
        height: 78px;
    }

    .loading-overlay .left-line-4,
    .loading-overlay .right-line-4 {
        left: 50%;
        height: 60px;
    }

    .loading-overlay .left-line-4 {
        transform: translateX(-64px) translateY(-112px) scaleY(0);
        transform-origin: 50% 100%;
        animation: left-line4 6000ms linear infinite;
        animation-fill-mode: forwards;
    }

    .loading-overlay .right-line-4 {
        transform: translateX(59px) translateY(-104px) scaleY(0);
        transform-origin: 50% 0%;
        animation: right-line4 6000ms linear infinite;
        animation-fill-mode: forwards;
    }

    .loading-overlay .left-line-5,
    .loading-overlay .right-line-5,
    .loading-overlay .right-line-5-wrap,
    .loading-overlay .left-line-5-wrap {
        left: 50%;
        height: 55px;
    }

    .loading-overlay .left-line-5,
    .loading-overlay .right-line-5 {
        width: 10px;
    }

    .loading-overlay .right-line-5-wrap {
        background-color: transparent;
        transform: translateY(-133px) translateX(16px);
        transform-origin: 50% 100%;
        clip-path: polygon(100% 0%, 0% 0%, 0% 100%, 100% 95.2%);
    }

@media (max-resolution: 120dpi) {
    .loading-overlay .right-line-5-wrap {
        clip-path: polygon(100% 0%, 0% 0%, 0% 102%, 100% 97.2%);
    }
}

.loading-overlay .left-line-5-wrap {
    background-color: transparent;
    transform: translateY(-80px) translateX(-21px);
    transform-origin: 50% 0%;
    clip-path: polygon(0% 100%, 0% 6.3%, 100% 1%, 100% 100%);
}

@media (max-resolution: 120dpi) {
    .loading-overlay .left-line-5-wrap {
        clip-path: polygon(0% 100%, 0% 8.3%, 100% 3%, 100% 100%);
    }
}

.loading-overlay .left-line-5 {
    transform: translateY(-2px) translateX(-4px) scaleY(0);
    transform-origin: 50% 0%;
    animation: left-line5 6000ms linear infinite;
    animation-fill-mode: forwards;
}

.loading-overlay .right-line-5 {
    transform: translateY(0px) translateX(-4px) scaleY(0);
    transform-origin: 50% 100%;
    animation: right-line5 6000ms linear infinite;
    animation-fill-mode: forwards;
    height: 56px;
}

.loading-overlay .left-line-6,
.loading-overlay .right-line-6 {
    left: 50%;
    height: 57px;
}

.loading-overlay .left-line-6 {
    transform: rotate(-58deg) translateY(-57px) translateX(59px) scaleY(0);
    transform-origin: 50% 100%;
    animation: left-line6 6000ms linear infinite;
    animation-fill-mode: forwards;
}

.loading-overlay .right-line-6 {
    transform: rotate(-59deg) translateY(-57px) translateX(120px) scaleY(0);
    transform-origin: 50% 0%;
    animation: right-line6 6000ms linear infinite;
    animation-fill-mode: forwards;
}

@keyframes left-line1 {
    0% {
        background-color: white;
        transform: rotate(59deg) translateX(-199px) translateY(-42px) scaleY(0);
    }

    12.5% {
        transform: rotate(59deg) translateX(-199px) translateY(-42px) scaleY(1);
    }

    79.5% {
        transform: rotate(59deg) translateX(-199px) translateY(-42px) scaleY(1);
    }

    86% {
        transform: rotate(59deg) translateX(-199px) translateY(-42px) scaleY(0);
        background-color: white;
    }
}

@keyframes right-line1 {
    0% {
        background-color: white;
        transform: rotate(59deg) translateX(-7px) translateY(-75px) scaleY(0);
    }

    12.5% {
        transform: rotate(59deg) translateX(-7px) translateY(-75px) scaleY(1);
    }

    79.5% {
        transform: rotate(59deg) translateX(-7px) translateY(-75px) scaleY(1);
    }

    86% {
        transform: rotate(59deg) translateX(-7px) translateY(-75px) scaleY(0);
        background-color: white;
    }
}

@keyframes left-line2 {
    12.5% {
        background-color: white;
        transform: translateY(-154px) translateX(2px) scaleY(0);
    }

    25% {
        transform: translateY(-154px) translateX(2px) scaleY(1);
    }

    75% {
        transform: translateY(-154px) translateX(2px) scaleY(1);
    }

    79.5% {
        transform: translateY(-154px) translateX(2px) scaleY(0);
        background-color: white;
    }
}

@keyframes right-line2 {
    12.5% {
        background-color: white;
        transform: translateY(-68px) translateX(-7px) scaleY(0);
    }

    25% {
        transform: translateY(-68px) translateX(-7px) scaleY(1);
    }

    75% {
        transform: translateY(-68px) translateX(-7px) scaleY(1);
    }

    79.5% {
        transform: translateY(-68px) translateX(-7px) scaleY(0);
        background-color: white;
    }
}

@keyframes left-line3 {
    25% {
        background-color: white;
        transform: rotate(59deg) translateX(-79px) translateY(-51px) scaleY(0);
    }

    39.5% {
        transform: rotate(59deg) translateX(-79px) translateY(-51px) scaleY(1);
    }

    62.5% {
        transform: rotate(59deg) translateX(-79px) translateY(-51px) scaleY(1);
    }

    75% {
        transform: rotate(59deg) translateX(-79px) translateY(-51px) scaleY(0);
        background-color: white;
    }
}

@keyframes right-line3 {
    25% {
        background-color: white;
        transform: rotate(59deg) translateX(-125px) translateY(-67px) scaleY(0);
    }

    39.5% {
        transform: rotate(59deg) translateX(-125px) translateY(-67px) scaleY(1);
    }

    62.5% {
        transform: rotate(59deg) translateX(-125px) translateY(-67px) scaleY(1);
    }

    75% {
        transform: rotate(59deg) translateX(-125px) translateY(-67px) scaleY(0);
        background-color: white;
    }
}

@keyframes left-line4 {
    39.5% {
        background-color: white;
        transform: translateX(-64px) translateY(-112px) scaleY(0);
    }

    50% {
        transform: translateX(-64px) translateY(-112px) scaleY(1);
    }

    57% {
        transform: translateX(-64px) translateY(-112px) scaleY(1);
    }

    62.5% {
        transform: translateX(-64px) translateY(-112px) scaleY(0);
        background-color: white;
    }
}

@keyframes right-line4 {
    39.5% {
        background-color: white;
        transform: translateX(59px) translateY(-104px) scaleY(0);
    }

    50% {
        transform: translateX(59px) translateY(-104px) scaleY(1);
    }

    57% {
        transform: translateX(59px) translateY(-104px) scaleY(1);
    }

    62.5% {
        transform: translateX(59px) translateY(-104px) scaleY(0);
        background-color: white;
    }
}

@keyframes left-line5 {
    28% {
        background-color: white;
        transform: translateY(-2px) translateX(-4px) scaleY(0);
    }

    33.25% {
        transform: translateY(-2px) translateX(-4px) scaleY(1);
    }

    70% {
        transform: translateY(-2px) translateX(-4px) scaleY(1);
    }

    78% {
        transform: translateY(-2px) translateX(-4px) scaleY(0);
        background-color: white;
    }
}

@keyframes right-line5 {
    28% {
        background-color: white;
        transform: translateY(0px) translateX(-4px) scaleY(0);
    }

    33.25% {
        transform: translateY(0px) translateX(-4px) scaleY(1);
    }

    70% {
        transform: translateY(0px) translateX(-4px) scaleY(1);
    }

    78% {
        transform: translateY(0px) translateX(-4px) scaleY(0);
        background-color: white;
    }
}

@keyframes left-line6 {
    33.25% {
        background-color: white;
        transform: rotate(-58deg) translateY(-57px) translateX(59px) scaleY(0);
    }

    39.5% {
        transform: rotate(-58deg) translateY(-57px) translateX(59px) scaleY(1);
    }

    62.5% {
        transform: rotate(-58deg) translateY(-57px) translateX(59px) scaleY(1);
    }

    70% {
        transform: rotate(-58deg) translateY(-57px) translateX(59px) scaleY(0);
        background-color: white;
    }
}

@keyframes right-line6 {
    33.25% {
        background-color: white;
        transform: rotate(-58deg) translateY(-57px) translateX(120px) scaleY(0);
    }

    39.5% {
        transform: rotate(-58deg) translateY(-57px) translateX(120px) scaleY(1);
    }

    62.5% {
        transform: rotate(-58deg) translateY(-57px) translateX(120px) scaleY(1);
    }

    70% {
        transform: rotate(-58deg) translateY(-57px) translateX(120px) scaleY(0);
        background-color: white;
    }
}
`, "",{"version":3,"sources":["webpack://./style/index.css"],"names":[],"mappings":"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","sourcesContent":["/*-----------------------------------------------------------------------------\n| Copyright (c) Jupyter Development Team.\n| Distributed under the terms of the Modified BSD License.\n|----------------------------------------------------------------------------*/\n\n@import './variables.css';\n\n/* Set the default typography for monospace elements */\ntt,\ncode,\nkbd,\nsamp,\npre {\n  font-family: var(--jp-code-font-family);\n  font-size: var(--jp-code-font-size);\n  line-height: var(--jp-code-line-height);\n}\n\n/* Top menubar styles */\n#jp-top-panel {\n    border-bottom: 0;\n    background: var(--jp-layout-color2);\n}\n\n#jp-menu-panel {\n    background: var(--jp-layout-color2);\n}\n\n.lm-MenuBar {\n    background: var(--jp-layout-color2);\n}\n\n.lm-MenuBar-item.lm-mod-active {\n    background: var(--jp-layout-color4);\n}\n\n/* Left expanded sidebar */\n#jp-left-stack {\n    border-right: 2px solid var(--jp-layout-color3);\n}\n\n/* Left sidebar styles */\n.jp-SideBar.lm-TabBar.jp-mod-left {\n    border: 0;\n}\n\n.jp-SideBar .lm-TabBar-tab {\n    border: none;\n    border-image: none;\n}\n\n.jp-SideBar .lm-TabBar-tab.lm-mod-current {\n    border: none;\n}\n\n/* Right sidebar */\n.jp-SideBar.lm-TabBar.jp-mod-right {\n    border: 0;\n}\n\n/* Button dialog style */\nbutton.jp-mod-styled.jp-mod-accept {\n    background-color: #3c8dbc;\n}\n\n/* Loading animation */\n\n.splash-fade {\n    animation: 0.5s fade-out forwards;\n}\n\n.loading-overlay {\n    z-index: 2000;\n    border: none;\n    margin: 0px;\n    padding: 0px;\n    width: 100%;\n    height: 100%;\n    top: 0;\n    left: 0;\n    background-color: white;\n    opacity: 0.9;\n    position: fixed;\n    text-align: center;\n}\n\n    .loading-overlay svg {\n        height: 150px;\n        width: 150px;\n    }\n\n    .loading-overlay .loading-svg {\n        width: 150px;\n        height: 150px;\n        position: absolute;\n        top: calc(50% - 65px);\n        left: calc(50% - 75px);\n    }\n\n    .loading-overlay .line {\n        width: 5px;\n        height: 200px;\n        position: absolute;\n        animation-delay: 1000ms;\n        background-color: white;\n    }\n\n    .loading-overlay .left-line-1,\n    .loading-overlay .right-line-1 {\n        left: 50%;\n        height: 81px;\n    }\n\n    .loading-overlay .left-line-1 {\n        transform: rotate(59deg) translateX(-199px) translateY(-42px) scaleY(0);\n        transform-origin: 50% 100%;\n        animation: left-line1 6000ms linear infinite;\n        animation-fill-mode: forwards;\n    }\n\n    .loading-overlay .right-line-1 {\n        transform: rotate(59deg) translateX(-7px) translateY(-75px) scaleY(0);\n        transform-origin: 50% 0%;\n        animation: right-line1 6000ms linear infinite;\n        animation-fill-mode: forwards;\n    }\n\n    .loading-overlay .left-line-2,\n    .loading-overlay .right-line-2 {\n        left: 50%;\n        height: 64px;\n    }\n\n    .loading-overlay .left-line-2 {\n        transform: translateY(-154px) translateX(2px) scaleY(0);\n        transform-origin: 50% 0%;\n        animation: left-line2 6000ms linear infinite;\n        animation-fill-mode: forwards;\n    }\n\n    .loading-overlay .right-line-2 {\n        transform: translateY(-68px) translateX(-7px) scaleY(0);\n        transform-origin: 50% 100%;\n        animation: right-line2 6000ms linear infinite;\n        animation-fill-mode: forwards;\n    }\n\n    .loading-overlay .left-line-3,\n    .loading-overlay .right-line-3 {\n        left: 50%;\n        height: 76px;\n    }\n\n    .loading-overlay .left-line-3 {\n        transform: rotate(59deg) translateX(-79px) translateY(-51px) scaleY(0);\n        transform-origin: 50% 0%;\n        animation: left-line3 6000ms linear infinite;\n        animation-fill-mode: forwards;\n    }\n\n    .loading-overlay .right-line-3 {\n        transform: rotate(59deg) translateX(-125px) translateY(-67px) scaleY(0);\n        transform-origin: 50% 100%;\n        animation: right-line3 6000ms linear infinite;\n        animation-fill-mode: forwards;\n        height: 78px;\n    }\n\n    .loading-overlay .left-line-4,\n    .loading-overlay .right-line-4 {\n        left: 50%;\n        height: 60px;\n    }\n\n    .loading-overlay .left-line-4 {\n        transform: translateX(-64px) translateY(-112px) scaleY(0);\n        transform-origin: 50% 100%;\n        animation: left-line4 6000ms linear infinite;\n        animation-fill-mode: forwards;\n    }\n\n    .loading-overlay .right-line-4 {\n        transform: translateX(59px) translateY(-104px) scaleY(0);\n        transform-origin: 50% 0%;\n        animation: right-line4 6000ms linear infinite;\n        animation-fill-mode: forwards;\n    }\n\n    .loading-overlay .left-line-5,\n    .loading-overlay .right-line-5,\n    .loading-overlay .right-line-5-wrap,\n    .loading-overlay .left-line-5-wrap {\n        left: 50%;\n        height: 55px;\n    }\n\n    .loading-overlay .left-line-5,\n    .loading-overlay .right-line-5 {\n        width: 10px;\n    }\n\n    .loading-overlay .right-line-5-wrap {\n        background-color: transparent;\n        transform: translateY(-133px) translateX(16px);\n        transform-origin: 50% 100%;\n        clip-path: polygon(100% 0%, 0% 0%, 0% 100%, 100% 95.2%);\n    }\n\n@media (max-resolution: 120dpi) {\n    .loading-overlay .right-line-5-wrap {\n        clip-path: polygon(100% 0%, 0% 0%, 0% 102%, 100% 97.2%);\n    }\n}\n\n.loading-overlay .left-line-5-wrap {\n    background-color: transparent;\n    transform: translateY(-80px) translateX(-21px);\n    transform-origin: 50% 0%;\n    clip-path: polygon(0% 100%, 0% 6.3%, 100% 1%, 100% 100%);\n}\n\n@media (max-resolution: 120dpi) {\n    .loading-overlay .left-line-5-wrap {\n        clip-path: polygon(0% 100%, 0% 8.3%, 100% 3%, 100% 100%);\n    }\n}\n\n.loading-overlay .left-line-5 {\n    transform: translateY(-2px) translateX(-4px) scaleY(0);\n    transform-origin: 50% 0%;\n    animation: left-line5 6000ms linear infinite;\n    animation-fill-mode: forwards;\n}\n\n.loading-overlay .right-line-5 {\n    transform: translateY(0px) translateX(-4px) scaleY(0);\n    transform-origin: 50% 100%;\n    animation: right-line5 6000ms linear infinite;\n    animation-fill-mode: forwards;\n    height: 56px;\n}\n\n.loading-overlay .left-line-6,\n.loading-overlay .right-line-6 {\n    left: 50%;\n    height: 57px;\n}\n\n.loading-overlay .left-line-6 {\n    transform: rotate(-58deg) translateY(-57px) translateX(59px) scaleY(0);\n    transform-origin: 50% 100%;\n    animation: left-line6 6000ms linear infinite;\n    animation-fill-mode: forwards;\n}\n\n.loading-overlay .right-line-6 {\n    transform: rotate(-59deg) translateY(-57px) translateX(120px) scaleY(0);\n    transform-origin: 50% 0%;\n    animation: right-line6 6000ms linear infinite;\n    animation-fill-mode: forwards;\n}\n\n@keyframes left-line1 {\n    0% {\n        background-color: white;\n        transform: rotate(59deg) translateX(-199px) translateY(-42px) scaleY(0);\n    }\n\n    12.5% {\n        transform: rotate(59deg) translateX(-199px) translateY(-42px) scaleY(1);\n    }\n\n    79.5% {\n        transform: rotate(59deg) translateX(-199px) translateY(-42px) scaleY(1);\n    }\n\n    86% {\n        transform: rotate(59deg) translateX(-199px) translateY(-42px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes right-line1 {\n    0% {\n        background-color: white;\n        transform: rotate(59deg) translateX(-7px) translateY(-75px) scaleY(0);\n    }\n\n    12.5% {\n        transform: rotate(59deg) translateX(-7px) translateY(-75px) scaleY(1);\n    }\n\n    79.5% {\n        transform: rotate(59deg) translateX(-7px) translateY(-75px) scaleY(1);\n    }\n\n    86% {\n        transform: rotate(59deg) translateX(-7px) translateY(-75px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes left-line2 {\n    12.5% {\n        background-color: white;\n        transform: translateY(-154px) translateX(2px) scaleY(0);\n    }\n\n    25% {\n        transform: translateY(-154px) translateX(2px) scaleY(1);\n    }\n\n    75% {\n        transform: translateY(-154px) translateX(2px) scaleY(1);\n    }\n\n    79.5% {\n        transform: translateY(-154px) translateX(2px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes right-line2 {\n    12.5% {\n        background-color: white;\n        transform: translateY(-68px) translateX(-7px) scaleY(0);\n    }\n\n    25% {\n        transform: translateY(-68px) translateX(-7px) scaleY(1);\n    }\n\n    75% {\n        transform: translateY(-68px) translateX(-7px) scaleY(1);\n    }\n\n    79.5% {\n        transform: translateY(-68px) translateX(-7px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes left-line3 {\n    25% {\n        background-color: white;\n        transform: rotate(59deg) translateX(-79px) translateY(-51px) scaleY(0);\n    }\n\n    39.5% {\n        transform: rotate(59deg) translateX(-79px) translateY(-51px) scaleY(1);\n    }\n\n    62.5% {\n        transform: rotate(59deg) translateX(-79px) translateY(-51px) scaleY(1);\n    }\n\n    75% {\n        transform: rotate(59deg) translateX(-79px) translateY(-51px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes right-line3 {\n    25% {\n        background-color: white;\n        transform: rotate(59deg) translateX(-125px) translateY(-67px) scaleY(0);\n    }\n\n    39.5% {\n        transform: rotate(59deg) translateX(-125px) translateY(-67px) scaleY(1);\n    }\n\n    62.5% {\n        transform: rotate(59deg) translateX(-125px) translateY(-67px) scaleY(1);\n    }\n\n    75% {\n        transform: rotate(59deg) translateX(-125px) translateY(-67px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes left-line4 {\n    39.5% {\n        background-color: white;\n        transform: translateX(-64px) translateY(-112px) scaleY(0);\n    }\n\n    50% {\n        transform: translateX(-64px) translateY(-112px) scaleY(1);\n    }\n\n    57% {\n        transform: translateX(-64px) translateY(-112px) scaleY(1);\n    }\n\n    62.5% {\n        transform: translateX(-64px) translateY(-112px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes right-line4 {\n    39.5% {\n        background-color: white;\n        transform: translateX(59px) translateY(-104px) scaleY(0);\n    }\n\n    50% {\n        transform: translateX(59px) translateY(-104px) scaleY(1);\n    }\n\n    57% {\n        transform: translateX(59px) translateY(-104px) scaleY(1);\n    }\n\n    62.5% {\n        transform: translateX(59px) translateY(-104px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes left-line5 {\n    28% {\n        background-color: white;\n        transform: translateY(-2px) translateX(-4px) scaleY(0);\n    }\n\n    33.25% {\n        transform: translateY(-2px) translateX(-4px) scaleY(1);\n    }\n\n    70% {\n        transform: translateY(-2px) translateX(-4px) scaleY(1);\n    }\n\n    78% {\n        transform: translateY(-2px) translateX(-4px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes right-line5 {\n    28% {\n        background-color: white;\n        transform: translateY(0px) translateX(-4px) scaleY(0);\n    }\n\n    33.25% {\n        transform: translateY(0px) translateX(-4px) scaleY(1);\n    }\n\n    70% {\n        transform: translateY(0px) translateX(-4px) scaleY(1);\n    }\n\n    78% {\n        transform: translateY(0px) translateX(-4px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes left-line6 {\n    33.25% {\n        background-color: white;\n        transform: rotate(-58deg) translateY(-57px) translateX(59px) scaleY(0);\n    }\n\n    39.5% {\n        transform: rotate(-58deg) translateY(-57px) translateX(59px) scaleY(1);\n    }\n\n    62.5% {\n        transform: rotate(-58deg) translateY(-57px) translateX(59px) scaleY(1);\n    }\n\n    70% {\n        transform: rotate(-58deg) translateY(-57px) translateX(59px) scaleY(0);\n        background-color: white;\n    }\n}\n\n@keyframes right-line6 {\n    33.25% {\n        background-color: white;\n        transform: rotate(-58deg) translateY(-57px) translateX(120px) scaleY(0);\n    }\n\n    39.5% {\n        transform: rotate(-58deg) translateY(-57px) translateX(120px) scaleY(1);\n    }\n\n    62.5% {\n        transform: rotate(-58deg) translateY(-57px) translateX(120px) scaleY(1);\n    }\n\n    70% {\n        transform: rotate(-58deg) translateY(-57px) translateX(120px) scaleY(0);\n        background-color: white;\n    }\n}\n"],"sourceRoot":""}]);
// Exports
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (___CSS_LOADER_EXPORT___);


/***/ }),

/***/ "./node_modules/css-loader/dist/cjs.js!./style/variables.css":
/*!*******************************************************************!*\
  !*** ./node_modules/css-loader/dist/cjs.js!./style/variables.css ***!
  \*******************************************************************/
/***/ ((module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _node_modules_css_loader_dist_runtime_sourceMaps_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../node_modules/css-loader/dist/runtime/sourceMaps.js */ "./node_modules/css-loader/dist/runtime/sourceMaps.js");
/* harmony import */ var _node_modules_css_loader_dist_runtime_sourceMaps_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_node_modules_css_loader_dist_runtime_sourceMaps_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../node_modules/css-loader/dist/runtime/api.js */ "./node_modules/css-loader/dist/runtime/api.js");
/* harmony import */ var _node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1__);
// Imports


var ___CSS_LOADER_EXPORT___ = _node_modules_css_loader_dist_runtime_api_js__WEBPACK_IMPORTED_MODULE_1___default()((_node_modules_css_loader_dist_runtime_sourceMaps_js__WEBPACK_IMPORTED_MODULE_0___default()));
// Module
___CSS_LOADER_EXPORT___.push([module.id, `/* ----------------------------------------------------------------------------
| Copyright (c) Jupyter Development Team.
| Distributed under the terms of the Modified BSD License.
|--------------------------------------------------------------------------- */

/*
The following CSS variables define the main, public API for styling JupyterLab.
These variables should be used by all plugins wherever possible. In other
words, plugins should not define custom colors, sizes, etc unless absolutely
necessary. This enables users to change the visual theme of JupyterLab
by changing these variables.

Many variables appear in an ordered sequence (0,1,2,3). These sequences
are designed to work well together, so for example, \`--jp-border-color1\` should
be used with \`--jp-layout-color1\`. The numbers have the following meanings:

* 0: super-primary, reserved for special emphasis
* 1: primary, most important under normal situations
* 2: secondary, next most important under normal situations
* 3: tertiary, next most important under normal situations

Throughout JupyterLab, we are mostly following principles from Google's
Material Design when selecting colors. We are not, however, following
all of MD as it is not optimized for dense, information rich UIs.
*/

:root {
  /* Elevation
   *
   * We style box-shadows using Material Design's idea of elevation. These particular numbers are taken from here:
   *
   * https://github.com/material-components/material-components-web
   * https://material-components-web.appspot.com/elevation.html
   */

  --jp-shadow-base-lightness: 0;
  --jp-shadow-umbra-color: rgba(
    var(--jp-shadow-base-lightness),
    var(--jp-shadow-base-lightness),
    var(--jp-shadow-base-lightness),
    0.2
  );
  --jp-shadow-penumbra-color: rgba(
    var(--jp-shadow-base-lightness),
    var(--jp-shadow-base-lightness),
    var(--jp-shadow-base-lightness),
    0.14
  );
  --jp-shadow-ambient-color: rgba(
    var(--jp-shadow-base-lightness),
    var(--jp-shadow-base-lightness),
    var(--jp-shadow-base-lightness),
    0.12
  );
  --jp-elevation-z0: none;
  --jp-elevation-z1:
    0 2px 1px -1px var(--jp-shadow-umbra-color),
    0 1px 1px 0 var(--jp-shadow-penumbra-color),
    0 1px 3px 0 var(--jp-shadow-ambient-color);
  --jp-elevation-z2:
    0 3px 1px -2px var(--jp-shadow-umbra-color),
    0 2px 2px 0 var(--jp-shadow-penumbra-color),
    0 1px 5px 0 var(--jp-shadow-ambient-color);
  --jp-elevation-z4:
    0 2px 4px -1px var(--jp-shadow-umbra-color),
    0 4px 5px 0 var(--jp-shadow-penumbra-color),
    0 1px 10px 0 var(--jp-shadow-ambient-color);
  --jp-elevation-z6:
    0 3px 5px -1px var(--jp-shadow-umbra-color),
    0 6px 10px 0 var(--jp-shadow-penumbra-color),
    0 1px 18px 0 var(--jp-shadow-ambient-color);
  --jp-elevation-z8:
    0 5px 5px -3px var(--jp-shadow-umbra-color),
    0 8px 10px 1px var(--jp-shadow-penumbra-color),
    0 3px 14px 2px var(--jp-shadow-ambient-color);
  --jp-elevation-z12:
    0 7px 8px -4px var(--jp-shadow-umbra-color),
    0 12px 17px 2px var(--jp-shadow-penumbra-color),
    0 5px 22px 4px var(--jp-shadow-ambient-color);
  --jp-elevation-z16:
    0 8px 10px -5px var(--jp-shadow-umbra-color),
    0 16px 24px 2px var(--jp-shadow-penumbra-color),
    0 6px 30px 5px var(--jp-shadow-ambient-color);
  --jp-elevation-z20:
    0 10px 13px -6px var(--jp-shadow-umbra-color),
    0 20px 31px 3px var(--jp-shadow-penumbra-color),
    0 8px 38px 7px var(--jp-shadow-ambient-color);
  --jp-elevation-z24:
    0 11px 15px -7px var(--jp-shadow-umbra-color),
    0 24px 38px 3px var(--jp-shadow-penumbra-color),
    0 9px 46px 8px var(--jp-shadow-ambient-color);

  /* Borders
   *
   * The following variables, specify the visual styling of borders in JupyterLab.
   */

  --jp-border-width: 1px;
  --jp-border-color0: var(--md-grey-400);
  --jp-border-color1: var(--md-grey-400);
  --jp-border-color2: var(--md-grey-300);
  --jp-border-color3: var(--md-grey-200);
  --jp-border-radius: 2px;

  /* UI Fonts
   *
   * The UI font CSS variables are used for the typography all of the JupyterLab
   * user interface elements that are not directly user generated content.
   *
   * The font sizing here is done assuming that the body font size of --jp-ui-font-size1
   * is applied to a parent element. When children elements, such as headings, are sized
   * in em all things will be computed relative to that body size.
   */

  --jp-ui-font-scale-factor: 1.2;
  --jp-ui-font-size0: 0.8333em;
  --jp-ui-font-size1: 13px; /* Base font size */
  --jp-ui-font-size2: 1.2em;
  --jp-ui-font-size3: 1.44em;
  --jp-ui-font-family:
    -apple-system, blinkmacsystemfont, 'Segoe UI', helvetica, arial, sans-serif,
    'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';

  /*
   * Use these font colors against the corresponding main layout colors.
   * In a light theme, these go from dark to light.
   */

  /* Defaults use Material Design specification */
  --jp-ui-font-color0: rgba(0, 0, 0, 1);
  --jp-ui-font-color1: rgba(0, 0, 0, 0.87);
  --jp-ui-font-color2: rgba(0, 0, 0, 0.54);
  --jp-ui-font-color3: rgba(0, 0, 0, 0.38);

  /*
   * Use these against the brand/accent/warn/error colors.
   * These will typically go from light to darker, in both a dark and light theme.
   */

  --jp-ui-inverse-font-color0: rgba(255, 255, 255, 1);
  --jp-ui-inverse-font-color1: rgba(255, 255, 255, 1);
  --jp-ui-inverse-font-color2: rgba(255, 255, 255, 0.7);
  --jp-ui-inverse-font-color3: rgba(255, 255, 255, 0.5);

  /* Content Fonts
   *
   * Content font variables are used for typography of user generated content.
   *
   * The font sizing here is done assuming that the body font size of --jp-content-font-size1
   * is applied to a parent element. When children elements, such as headings, are sized
   * in em all things will be computed relative to that body size.
   */

  --jp-content-line-height: 1.6;
  --jp-content-font-scale-factor: 1.2;
  --jp-content-font-size0: 0.8333em;
  --jp-content-font-size1: 14px; /* Base font size */
  --jp-content-font-size2: 1.2em;
  --jp-content-font-size3: 1.44em;
  --jp-content-font-size4: 1.728em;
  --jp-content-font-size5: 2.0736em;

  /* This gives a magnification of about 125% in presentation mode over normal. */
  --jp-content-presentation-font-size1: 17px;
  --jp-content-heading-line-height: 1;
  --jp-content-heading-margin-top: 1.2em;
  --jp-content-heading-margin-bottom: 0.8em;
  --jp-content-heading-font-weight: 500;

  /* Defaults use Material Design specification */
  --jp-content-font-color0: rgba(0, 0, 0, 1);
  --jp-content-font-color1: rgba(0, 0, 0, 0.87);
  --jp-content-font-color2: rgba(0, 0, 0, 0.54);
  --jp-content-font-color3: rgba(0, 0, 0, 0.38);
  --jp-content-link-color: var(--md-blue-700);
  --jp-content-font-family:
    -apple-system, blinkmacsystemfont, 'Segoe UI', helvetica, arial, sans-serif,
    'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';

  /*
   * Code Fonts
   *
   * Code font variables are used for typography of code and other monospaces content.
   */

  --jp-code-font-size: 13px;
  --jp-code-line-height: 1.3077; /* 17px for 13px base */
  --jp-code-padding: 0.385em; /* 5px for 13px base */
  --jp-code-font-family-default: menlo, consolas, 'DejaVu Sans Mono', monospace;
  --jp-code-font-family: var(--jp-code-font-family-default);

  /* This gives a magnification of about 125% in presentation mode over normal. */
  --jp-code-presentation-font-size: 16px;

  /* may need to tweak cursor width if you change font size */
  --jp-code-cursor-width0: 1.4px;
  --jp-code-cursor-width1: 2px;
  --jp-code-cursor-width2: 4px;

  /* Layout
   *
   * The following are the main layout colors use in JupyterLab. In a light
   * theme these would go from light to dark.
   */

  --jp-layout-color0: white;
  --jp-layout-color1: white;
  --jp-layout-color2: var(--md-grey-200);
  --jp-layout-color3: var(--md-grey-400);
  --jp-layout-color4: var(--md-grey-600);

  /* Inverse Layout
   *
   * The following are the inverse layout colors use in JupyterLab. In a light
   * theme these would go from dark to light.
   */

  --jp-inverse-layout-color0: #111;
  --jp-inverse-layout-color1: var(--md-grey-900);
  --jp-inverse-layout-color2: var(--md-grey-800);
  --jp-inverse-layout-color3: var(--md-grey-700);
  --jp-inverse-layout-color4: var(--md-grey-600);

  /* Brand/accent */

  --jp-brand-color0: #ec0c4b;
  --jp-brand-color1: #ed225d;
  --jp-brand-color2: #ee376b;
  --jp-brand-color3: #ee3b6e;
  --jp-accent-color0: var(--md-green-700);
  --jp-accent-color1: var(--md-green-500);
  --jp-accent-color2: var(--md-green-300);
  --jp-accent-color3: var(--md-green-100);

  /* State colors (warn, error, success, info) */

  --jp-warn-color0: var(--md-orange-700);
  --jp-warn-color1: var(--md-orange-500);
  --jp-warn-color2: var(--md-orange-300);
  --jp-warn-color3: var(--md-orange-100);
  --jp-error-color0: var(--md-red-700);
  --jp-error-color1: var(--md-red-500);
  --jp-error-color2: var(--md-red-300);
  --jp-error-color3: var(--md-red-100);
  --jp-success-color0: var(--md-green-700);
  --jp-success-color1: var(--md-green-500);
  --jp-success-color2: var(--md-green-300);
  --jp-success-color3: var(--md-green-100);
  --jp-info-color0: var(--md-cyan-700);
  --jp-info-color1: var(--md-cyan-500);
  --jp-info-color2: var(--md-cyan-300);
  --jp-info-color3: var(--md-cyan-100);

  /* Cell specific styles */

  --jp-cell-padding: 5px;
  --jp-cell-collapser-width: 8px;
  --jp-cell-collapser-min-height: 20px;
  --jp-cell-collapser-not-active-hover-opacity: 0.6;
  --jp-cell-editor-background: var(--md-grey-100);
  --jp-cell-editor-border-color: var(--md-grey-300);
  --jp-cell-editor-box-shadow: inset 0 0 2px var(--md-blue-300);
  --jp-cell-editor-active-background: var(--jp-layout-color0);
  --jp-cell-editor-active-border-color: var(--jp-brand-color1);
  --jp-cell-prompt-width: 64px;
  --jp-cell-prompt-font-family: 'Source Code Pro', monospace;
  --jp-cell-prompt-letter-spacing: 0;
  --jp-cell-prompt-opacity: 1;
  --jp-cell-prompt-not-active-opacity: 0.5;
  --jp-cell-prompt-not-active-font-color: var(--md-grey-700);

  /* A custom blend of MD grey and blue 600
   * See https://meyerweb.com/eric/tools/color-blend/#546E7A:1E88E5:5:hex */
  --jp-cell-inprompt-font-color: #307fc1;

  /* A custom blend of MD grey and orange 600
   * https://meyerweb.com/eric/tools/color-blend/#546E7A:F4511E:5:hex */
  --jp-cell-outprompt-font-color: #bf5b3d;

  /* Notebook specific styles */

  --jp-notebook-padding: 10px;
  --jp-notebook-select-background: var(--jp-layout-color1);
  --jp-notebook-multiselected-color: var(--md-blue-50);

  /* The scroll padding is calculated to fill enough space at the bottom of the
  notebook to show one single-line cell (with appropriate padding) at the top
  when the notebook is scrolled all the way to the bottom. We also subtract one
  pixel so that no scrollbar appears if we have just one single-line cell in the
  notebook. This padding is to enable a 'scroll past end' feature in a notebook.
  */
  --jp-notebook-scroll-padding: calc(
    100% - var(--jp-code-font-size) * var(--jp-code-line-height) -
      var(--jp-code-padding) - var(--jp-cell-padding) - 1px
  );

  /* Rendermime styles */

  --jp-rendermime-error-background: #fdd;
  --jp-rendermime-table-row-background: var(--md-grey-100);
  --jp-rendermime-table-row-hover-background: var(--md-light-blue-50);

  /* Dialog specific styles */

  --jp-dialog-background: rgba(0, 0, 0, 0.25);

  /* Console specific styles */

  --jp-console-padding: 10px;

  /* Toolbar specific styles */

  --jp-toolbar-border-color: var(--jp-border-color1);
  --jp-toolbar-micro-height: 8px;
  --jp-toolbar-background: var(--jp-layout-color1);
  --jp-toolbar-box-shadow: 0 0 2px 0 rgba(0, 0, 0, 0.24);
  --jp-toolbar-header-margin: 4px 4px 0 4px;
  --jp-toolbar-active-background: var(--md-grey-300);

  /* Statusbar specific styles */

  --jp-statusbar-height: 24px;

  /* Input field styles */

  --jp-input-box-shadow: inset 0 0 2px var(--md-blue-300);
  --jp-input-active-background: var(--jp-layout-color1);
  --jp-input-hover-background: var(--jp-layout-color1);
  --jp-input-background: var(--md-grey-100);
  --jp-input-border-color: var(--jp-border-color1);
  --jp-input-active-border-color: var(--jp-brand-color1);

  /* General editor styles */

  --jp-editor-selected-background: #d9d9d9;
  --jp-editor-selected-focused-background: #d7d4f0;
  --jp-editor-cursor-color: var(--jp-ui-font-color0);

  /* Code mirror specific styles */

  --jp-mirror-editor-keyword-color: #008000;
  --jp-mirror-editor-atom-color: #88f;
  --jp-mirror-editor-number-color: #080;
  --jp-mirror-editor-def-color: #00f;
  --jp-mirror-editor-variable-color: var(--md-grey-900);
  --jp-mirror-editor-variable-2-color: #05a;
  --jp-mirror-editor-variable-3-color: #085;
  --jp-mirror-editor-punctuation-color: #05a;
  --jp-mirror-editor-property-color: #05a;
  --jp-mirror-editor-operator-color: #a2f;
  --jp-mirror-editor-comment-color: #408080;
  --jp-mirror-editor-string-color: #ba2121;
  --jp-mirror-editor-string-2-color: #708;
  --jp-mirror-editor-meta-color: #a2f;
  --jp-mirror-editor-qualifier-color: #555;
  --jp-mirror-editor-builtin-color: #008000;
  --jp-mirror-editor-bracket-color: #997;
  --jp-mirror-editor-tag-color: #170;
  --jp-mirror-editor-attribute-color: #00c;
  --jp-mirror-editor-header-color: blue;
  --jp-mirror-editor-quote-color: #090;
  --jp-mirror-editor-link-color: #00c;
  --jp-mirror-editor-error-color: #f00;
  --jp-mirror-editor-hr-color: #999;

  /* User colors */

  --jp-collaborator-color1: #ad4a00;
  --jp-collaborator-color2: #7b6a00;
  --jp-collaborator-color3: #007e00;
  --jp-collaborator-color4: #008772;
  --jp-collaborator-color5: #0079b9;
  --jp-collaborator-color6: #8b45c6;
  --jp-collaborator-color7: #be208b;

  /* File or activity icons and switch semantic variables */

  --jp-jupyter-icon-color: var(--md-orange-900);
  --jp-notebook-icon-color: var(--md-orange-700);
  --jp-json-icon-color: var(--md-orange-700);
  --jp-console-icon-background-color: var(--md-blue-700);
  --jp-console-icon-color: white;
  --jp-terminal-icon-background-color: var(--md-grey-200);
  --jp-terminal-icon-color: var(--md-grey-800);
  --jp-text-editor-icon-color: var(--md-grey-200);
  --jp-inspector-icon-color: var(--md-grey-200);
  --jp-switch-color: var(--md-grey-400);
  --jp-switch-true-position-color: var(--md-orange-700);
  --jp-switch-cursor-color: rgba(0, 0, 0, 0.8);

  /* Vega extension styles */

  --jp-vega-background: white;

  /* Sidebar-related styles */

  --jp-sidebar-min-width: 180px;
}
`, "",{"version":3,"sources":["webpack://./style/variables.css"],"names":[],"mappings":"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","sourcesContent":["/* ----------------------------------------------------------------------------\r\n| Copyright (c) Jupyter Development Team.\r\n| Distributed under the terms of the Modified BSD License.\r\n|--------------------------------------------------------------------------- */\r\n\r\n/*\r\nThe following CSS variables define the main, public API for styling JupyterLab.\r\nThese variables should be used by all plugins wherever possible. In other\r\nwords, plugins should not define custom colors, sizes, etc unless absolutely\r\nnecessary. This enables users to change the visual theme of JupyterLab\r\nby changing these variables.\r\n\r\nMany variables appear in an ordered sequence (0,1,2,3). These sequences\r\nare designed to work well together, so for example, `--jp-border-color1` should\r\nbe used with `--jp-layout-color1`. The numbers have the following meanings:\r\n\r\n* 0: super-primary, reserved for special emphasis\r\n* 1: primary, most important under normal situations\r\n* 2: secondary, next most important under normal situations\r\n* 3: tertiary, next most important under normal situations\r\n\r\nThroughout JupyterLab, we are mostly following principles from Google's\r\nMaterial Design when selecting colors. We are not, however, following\r\nall of MD as it is not optimized for dense, information rich UIs.\r\n*/\r\n\r\n:root {\r\n  /* Elevation\r\n   *\r\n   * We style box-shadows using Material Design's idea of elevation. These particular numbers are taken from here:\r\n   *\r\n   * https://github.com/material-components/material-components-web\r\n   * https://material-components-web.appspot.com/elevation.html\r\n   */\r\n\r\n  --jp-shadow-base-lightness: 0;\r\n  --jp-shadow-umbra-color: rgba(\r\n    var(--jp-shadow-base-lightness),\r\n    var(--jp-shadow-base-lightness),\r\n    var(--jp-shadow-base-lightness),\r\n    0.2\r\n  );\r\n  --jp-shadow-penumbra-color: rgba(\r\n    var(--jp-shadow-base-lightness),\r\n    var(--jp-shadow-base-lightness),\r\n    var(--jp-shadow-base-lightness),\r\n    0.14\r\n  );\r\n  --jp-shadow-ambient-color: rgba(\r\n    var(--jp-shadow-base-lightness),\r\n    var(--jp-shadow-base-lightness),\r\n    var(--jp-shadow-base-lightness),\r\n    0.12\r\n  );\r\n  --jp-elevation-z0: none;\r\n  --jp-elevation-z1:\r\n    0 2px 1px -1px var(--jp-shadow-umbra-color),\r\n    0 1px 1px 0 var(--jp-shadow-penumbra-color),\r\n    0 1px 3px 0 var(--jp-shadow-ambient-color);\r\n  --jp-elevation-z2:\r\n    0 3px 1px -2px var(--jp-shadow-umbra-color),\r\n    0 2px 2px 0 var(--jp-shadow-penumbra-color),\r\n    0 1px 5px 0 var(--jp-shadow-ambient-color);\r\n  --jp-elevation-z4:\r\n    0 2px 4px -1px var(--jp-shadow-umbra-color),\r\n    0 4px 5px 0 var(--jp-shadow-penumbra-color),\r\n    0 1px 10px 0 var(--jp-shadow-ambient-color);\r\n  --jp-elevation-z6:\r\n    0 3px 5px -1px var(--jp-shadow-umbra-color),\r\n    0 6px 10px 0 var(--jp-shadow-penumbra-color),\r\n    0 1px 18px 0 var(--jp-shadow-ambient-color);\r\n  --jp-elevation-z8:\r\n    0 5px 5px -3px var(--jp-shadow-umbra-color),\r\n    0 8px 10px 1px var(--jp-shadow-penumbra-color),\r\n    0 3px 14px 2px var(--jp-shadow-ambient-color);\r\n  --jp-elevation-z12:\r\n    0 7px 8px -4px var(--jp-shadow-umbra-color),\r\n    0 12px 17px 2px var(--jp-shadow-penumbra-color),\r\n    0 5px 22px 4px var(--jp-shadow-ambient-color);\r\n  --jp-elevation-z16:\r\n    0 8px 10px -5px var(--jp-shadow-umbra-color),\r\n    0 16px 24px 2px var(--jp-shadow-penumbra-color),\r\n    0 6px 30px 5px var(--jp-shadow-ambient-color);\r\n  --jp-elevation-z20:\r\n    0 10px 13px -6px var(--jp-shadow-umbra-color),\r\n    0 20px 31px 3px var(--jp-shadow-penumbra-color),\r\n    0 8px 38px 7px var(--jp-shadow-ambient-color);\r\n  --jp-elevation-z24:\r\n    0 11px 15px -7px var(--jp-shadow-umbra-color),\r\n    0 24px 38px 3px var(--jp-shadow-penumbra-color),\r\n    0 9px 46px 8px var(--jp-shadow-ambient-color);\r\n\r\n  /* Borders\r\n   *\r\n   * The following variables, specify the visual styling of borders in JupyterLab.\r\n   */\r\n\r\n  --jp-border-width: 1px;\r\n  --jp-border-color0: var(--md-grey-400);\r\n  --jp-border-color1: var(--md-grey-400);\r\n  --jp-border-color2: var(--md-grey-300);\r\n  --jp-border-color3: var(--md-grey-200);\r\n  --jp-border-radius: 2px;\r\n\r\n  /* UI Fonts\r\n   *\r\n   * The UI font CSS variables are used for the typography all of the JupyterLab\r\n   * user interface elements that are not directly user generated content.\r\n   *\r\n   * The font sizing here is done assuming that the body font size of --jp-ui-font-size1\r\n   * is applied to a parent element. When children elements, such as headings, are sized\r\n   * in em all things will be computed relative to that body size.\r\n   */\r\n\r\n  --jp-ui-font-scale-factor: 1.2;\r\n  --jp-ui-font-size0: 0.8333em;\r\n  --jp-ui-font-size1: 13px; /* Base font size */\r\n  --jp-ui-font-size2: 1.2em;\r\n  --jp-ui-font-size3: 1.44em;\r\n  --jp-ui-font-family:\r\n    -apple-system, blinkmacsystemfont, 'Segoe UI', helvetica, arial, sans-serif,\r\n    'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';\r\n\r\n  /*\r\n   * Use these font colors against the corresponding main layout colors.\r\n   * In a light theme, these go from dark to light.\r\n   */\r\n\r\n  /* Defaults use Material Design specification */\r\n  --jp-ui-font-color0: rgba(0, 0, 0, 1);\r\n  --jp-ui-font-color1: rgba(0, 0, 0, 0.87);\r\n  --jp-ui-font-color2: rgba(0, 0, 0, 0.54);\r\n  --jp-ui-font-color3: rgba(0, 0, 0, 0.38);\r\n\r\n  /*\r\n   * Use these against the brand/accent/warn/error colors.\r\n   * These will typically go from light to darker, in both a dark and light theme.\r\n   */\r\n\r\n  --jp-ui-inverse-font-color0: rgba(255, 255, 255, 1);\r\n  --jp-ui-inverse-font-color1: rgba(255, 255, 255, 1);\r\n  --jp-ui-inverse-font-color2: rgba(255, 255, 255, 0.7);\r\n  --jp-ui-inverse-font-color3: rgba(255, 255, 255, 0.5);\r\n\r\n  /* Content Fonts\r\n   *\r\n   * Content font variables are used for typography of user generated content.\r\n   *\r\n   * The font sizing here is done assuming that the body font size of --jp-content-font-size1\r\n   * is applied to a parent element. When children elements, such as headings, are sized\r\n   * in em all things will be computed relative to that body size.\r\n   */\r\n\r\n  --jp-content-line-height: 1.6;\r\n  --jp-content-font-scale-factor: 1.2;\r\n  --jp-content-font-size0: 0.8333em;\r\n  --jp-content-font-size1: 14px; /* Base font size */\r\n  --jp-content-font-size2: 1.2em;\r\n  --jp-content-font-size3: 1.44em;\r\n  --jp-content-font-size4: 1.728em;\r\n  --jp-content-font-size5: 2.0736em;\r\n\r\n  /* This gives a magnification of about 125% in presentation mode over normal. */\r\n  --jp-content-presentation-font-size1: 17px;\r\n  --jp-content-heading-line-height: 1;\r\n  --jp-content-heading-margin-top: 1.2em;\r\n  --jp-content-heading-margin-bottom: 0.8em;\r\n  --jp-content-heading-font-weight: 500;\r\n\r\n  /* Defaults use Material Design specification */\r\n  --jp-content-font-color0: rgba(0, 0, 0, 1);\r\n  --jp-content-font-color1: rgba(0, 0, 0, 0.87);\r\n  --jp-content-font-color2: rgba(0, 0, 0, 0.54);\r\n  --jp-content-font-color3: rgba(0, 0, 0, 0.38);\r\n  --jp-content-link-color: var(--md-blue-700);\r\n  --jp-content-font-family:\r\n    -apple-system, blinkmacsystemfont, 'Segoe UI', helvetica, arial, sans-serif,\r\n    'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';\r\n\r\n  /*\r\n   * Code Fonts\r\n   *\r\n   * Code font variables are used for typography of code and other monospaces content.\r\n   */\r\n\r\n  --jp-code-font-size: 13px;\r\n  --jp-code-line-height: 1.3077; /* 17px for 13px base */\r\n  --jp-code-padding: 0.385em; /* 5px for 13px base */\r\n  --jp-code-font-family-default: menlo, consolas, 'DejaVu Sans Mono', monospace;\r\n  --jp-code-font-family: var(--jp-code-font-family-default);\r\n\r\n  /* This gives a magnification of about 125% in presentation mode over normal. */\r\n  --jp-code-presentation-font-size: 16px;\r\n\r\n  /* may need to tweak cursor width if you change font size */\r\n  --jp-code-cursor-width0: 1.4px;\r\n  --jp-code-cursor-width1: 2px;\r\n  --jp-code-cursor-width2: 4px;\r\n\r\n  /* Layout\r\n   *\r\n   * The following are the main layout colors use in JupyterLab. In a light\r\n   * theme these would go from light to dark.\r\n   */\r\n\r\n  --jp-layout-color0: white;\r\n  --jp-layout-color1: white;\r\n  --jp-layout-color2: var(--md-grey-200);\r\n  --jp-layout-color3: var(--md-grey-400);\r\n  --jp-layout-color4: var(--md-grey-600);\r\n\r\n  /* Inverse Layout\r\n   *\r\n   * The following are the inverse layout colors use in JupyterLab. In a light\r\n   * theme these would go from dark to light.\r\n   */\r\n\r\n  --jp-inverse-layout-color0: #111;\r\n  --jp-inverse-layout-color1: var(--md-grey-900);\r\n  --jp-inverse-layout-color2: var(--md-grey-800);\r\n  --jp-inverse-layout-color3: var(--md-grey-700);\r\n  --jp-inverse-layout-color4: var(--md-grey-600);\r\n\r\n  /* Brand/accent */\r\n\r\n  --jp-brand-color0: #ec0c4b;\r\n  --jp-brand-color1: #ed225d;\r\n  --jp-brand-color2: #ee376b;\r\n  --jp-brand-color3: #ee3b6e;\r\n  --jp-accent-color0: var(--md-green-700);\r\n  --jp-accent-color1: var(--md-green-500);\r\n  --jp-accent-color2: var(--md-green-300);\r\n  --jp-accent-color3: var(--md-green-100);\r\n\r\n  /* State colors (warn, error, success, info) */\r\n\r\n  --jp-warn-color0: var(--md-orange-700);\r\n  --jp-warn-color1: var(--md-orange-500);\r\n  --jp-warn-color2: var(--md-orange-300);\r\n  --jp-warn-color3: var(--md-orange-100);\r\n  --jp-error-color0: var(--md-red-700);\r\n  --jp-error-color1: var(--md-red-500);\r\n  --jp-error-color2: var(--md-red-300);\r\n  --jp-error-color3: var(--md-red-100);\r\n  --jp-success-color0: var(--md-green-700);\r\n  --jp-success-color1: var(--md-green-500);\r\n  --jp-success-color2: var(--md-green-300);\r\n  --jp-success-color3: var(--md-green-100);\r\n  --jp-info-color0: var(--md-cyan-700);\r\n  --jp-info-color1: var(--md-cyan-500);\r\n  --jp-info-color2: var(--md-cyan-300);\r\n  --jp-info-color3: var(--md-cyan-100);\r\n\r\n  /* Cell specific styles */\r\n\r\n  --jp-cell-padding: 5px;\r\n  --jp-cell-collapser-width: 8px;\r\n  --jp-cell-collapser-min-height: 20px;\r\n  --jp-cell-collapser-not-active-hover-opacity: 0.6;\r\n  --jp-cell-editor-background: var(--md-grey-100);\r\n  --jp-cell-editor-border-color: var(--md-grey-300);\r\n  --jp-cell-editor-box-shadow: inset 0 0 2px var(--md-blue-300);\r\n  --jp-cell-editor-active-background: var(--jp-layout-color0);\r\n  --jp-cell-editor-active-border-color: var(--jp-brand-color1);\r\n  --jp-cell-prompt-width: 64px;\r\n  --jp-cell-prompt-font-family: 'Source Code Pro', monospace;\r\n  --jp-cell-prompt-letter-spacing: 0;\r\n  --jp-cell-prompt-opacity: 1;\r\n  --jp-cell-prompt-not-active-opacity: 0.5;\r\n  --jp-cell-prompt-not-active-font-color: var(--md-grey-700);\r\n\r\n  /* A custom blend of MD grey and blue 600\r\n   * See https://meyerweb.com/eric/tools/color-blend/#546E7A:1E88E5:5:hex */\r\n  --jp-cell-inprompt-font-color: #307fc1;\r\n\r\n  /* A custom blend of MD grey and orange 600\r\n   * https://meyerweb.com/eric/tools/color-blend/#546E7A:F4511E:5:hex */\r\n  --jp-cell-outprompt-font-color: #bf5b3d;\r\n\r\n  /* Notebook specific styles */\r\n\r\n  --jp-notebook-padding: 10px;\r\n  --jp-notebook-select-background: var(--jp-layout-color1);\r\n  --jp-notebook-multiselected-color: var(--md-blue-50);\r\n\r\n  /* The scroll padding is calculated to fill enough space at the bottom of the\r\n  notebook to show one single-line cell (with appropriate padding) at the top\r\n  when the notebook is scrolled all the way to the bottom. We also subtract one\r\n  pixel so that no scrollbar appears if we have just one single-line cell in the\r\n  notebook. This padding is to enable a 'scroll past end' feature in a notebook.\r\n  */\r\n  --jp-notebook-scroll-padding: calc(\r\n    100% - var(--jp-code-font-size) * var(--jp-code-line-height) -\r\n      var(--jp-code-padding) - var(--jp-cell-padding) - 1px\r\n  );\r\n\r\n  /* Rendermime styles */\r\n\r\n  --jp-rendermime-error-background: #fdd;\r\n  --jp-rendermime-table-row-background: var(--md-grey-100);\r\n  --jp-rendermime-table-row-hover-background: var(--md-light-blue-50);\r\n\r\n  /* Dialog specific styles */\r\n\r\n  --jp-dialog-background: rgba(0, 0, 0, 0.25);\r\n\r\n  /* Console specific styles */\r\n\r\n  --jp-console-padding: 10px;\r\n\r\n  /* Toolbar specific styles */\r\n\r\n  --jp-toolbar-border-color: var(--jp-border-color1);\r\n  --jp-toolbar-micro-height: 8px;\r\n  --jp-toolbar-background: var(--jp-layout-color1);\r\n  --jp-toolbar-box-shadow: 0 0 2px 0 rgba(0, 0, 0, 0.24);\r\n  --jp-toolbar-header-margin: 4px 4px 0 4px;\r\n  --jp-toolbar-active-background: var(--md-grey-300);\r\n\r\n  /* Statusbar specific styles */\r\n\r\n  --jp-statusbar-height: 24px;\r\n\r\n  /* Input field styles */\r\n\r\n  --jp-input-box-shadow: inset 0 0 2px var(--md-blue-300);\r\n  --jp-input-active-background: var(--jp-layout-color1);\r\n  --jp-input-hover-background: var(--jp-layout-color1);\r\n  --jp-input-background: var(--md-grey-100);\r\n  --jp-input-border-color: var(--jp-border-color1);\r\n  --jp-input-active-border-color: var(--jp-brand-color1);\r\n\r\n  /* General editor styles */\r\n\r\n  --jp-editor-selected-background: #d9d9d9;\r\n  --jp-editor-selected-focused-background: #d7d4f0;\r\n  --jp-editor-cursor-color: var(--jp-ui-font-color0);\r\n\r\n  /* Code mirror specific styles */\r\n\r\n  --jp-mirror-editor-keyword-color: #008000;\r\n  --jp-mirror-editor-atom-color: #88f;\r\n  --jp-mirror-editor-number-color: #080;\r\n  --jp-mirror-editor-def-color: #00f;\r\n  --jp-mirror-editor-variable-color: var(--md-grey-900);\r\n  --jp-mirror-editor-variable-2-color: #05a;\r\n  --jp-mirror-editor-variable-3-color: #085;\r\n  --jp-mirror-editor-punctuation-color: #05a;\r\n  --jp-mirror-editor-property-color: #05a;\r\n  --jp-mirror-editor-operator-color: #a2f;\r\n  --jp-mirror-editor-comment-color: #408080;\r\n  --jp-mirror-editor-string-color: #ba2121;\r\n  --jp-mirror-editor-string-2-color: #708;\r\n  --jp-mirror-editor-meta-color: #a2f;\r\n  --jp-mirror-editor-qualifier-color: #555;\r\n  --jp-mirror-editor-builtin-color: #008000;\r\n  --jp-mirror-editor-bracket-color: #997;\r\n  --jp-mirror-editor-tag-color: #170;\r\n  --jp-mirror-editor-attribute-color: #00c;\r\n  --jp-mirror-editor-header-color: blue;\r\n  --jp-mirror-editor-quote-color: #090;\r\n  --jp-mirror-editor-link-color: #00c;\r\n  --jp-mirror-editor-error-color: #f00;\r\n  --jp-mirror-editor-hr-color: #999;\r\n\r\n  /* User colors */\r\n\r\n  --jp-collaborator-color1: #ad4a00;\r\n  --jp-collaborator-color2: #7b6a00;\r\n  --jp-collaborator-color3: #007e00;\r\n  --jp-collaborator-color4: #008772;\r\n  --jp-collaborator-color5: #0079b9;\r\n  --jp-collaborator-color6: #8b45c6;\r\n  --jp-collaborator-color7: #be208b;\r\n\r\n  /* File or activity icons and switch semantic variables */\r\n\r\n  --jp-jupyter-icon-color: var(--md-orange-900);\r\n  --jp-notebook-icon-color: var(--md-orange-700);\r\n  --jp-json-icon-color: var(--md-orange-700);\r\n  --jp-console-icon-background-color: var(--md-blue-700);\r\n  --jp-console-icon-color: white;\r\n  --jp-terminal-icon-background-color: var(--md-grey-200);\r\n  --jp-terminal-icon-color: var(--md-grey-800);\r\n  --jp-text-editor-icon-color: var(--md-grey-200);\r\n  --jp-inspector-icon-color: var(--md-grey-200);\r\n  --jp-switch-color: var(--md-grey-400);\r\n  --jp-switch-true-position-color: var(--md-orange-700);\r\n  --jp-switch-cursor-color: rgba(0, 0, 0, 0.8);\r\n\r\n  /* Vega extension styles */\r\n\r\n  --jp-vega-background: white;\r\n\r\n  /* Sidebar-related styles */\r\n\r\n  --jp-sidebar-min-width: 180px;\r\n}\r\n"],"sourceRoot":""}]);
// Exports
/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (___CSS_LOADER_EXPORT___);


/***/ }),

/***/ "./node_modules/css-loader/dist/runtime/api.js":
/*!*****************************************************!*\
  !*** ./node_modules/css-loader/dist/runtime/api.js ***!
  \*****************************************************/
/***/ ((module) => {



/*
  MIT License http://www.opensource.org/licenses/mit-license.php
  Author Tobias Koppers @sokra
*/
module.exports = function (cssWithMappingToString) {
  var list = [];

  // return the list of modules as css string
  list.toString = function toString() {
    return this.map(function (item) {
      var content = "";
      var needLayer = typeof item[5] !== "undefined";
      if (item[4]) {
        content += "@supports (".concat(item[4], ") {");
      }
      if (item[2]) {
        content += "@media ".concat(item[2], " {");
      }
      if (needLayer) {
        content += "@layer".concat(item[5].length > 0 ? " ".concat(item[5]) : "", " {");
      }
      content += cssWithMappingToString(item);
      if (needLayer) {
        content += "}";
      }
      if (item[2]) {
        content += "}";
      }
      if (item[4]) {
        content += "}";
      }
      return content;
    }).join("");
  };

  // import a list of modules into the list
  list.i = function i(modules, media, dedupe, supports, layer) {
    if (typeof modules === "string") {
      modules = [[null, modules, undefined]];
    }
    var alreadyImportedModules = {};
    if (dedupe) {
      for (var k = 0; k < this.length; k++) {
        var id = this[k][0];
        if (id != null) {
          alreadyImportedModules[id] = true;
        }
      }
    }
    for (var _k = 0; _k < modules.length; _k++) {
      var item = [].concat(modules[_k]);
      if (dedupe && alreadyImportedModules[item[0]]) {
        continue;
      }
      if (typeof layer !== "undefined") {
        if (typeof item[5] === "undefined") {
          item[5] = layer;
        } else {
          item[1] = "@layer".concat(item[5].length > 0 ? " ".concat(item[5]) : "", " {").concat(item[1], "}");
          item[5] = layer;
        }
      }
      if (media) {
        if (!item[2]) {
          item[2] = media;
        } else {
          item[1] = "@media ".concat(item[2], " {").concat(item[1], "}");
          item[2] = media;
        }
      }
      if (supports) {
        if (!item[4]) {
          item[4] = "".concat(supports);
        } else {
          item[1] = "@supports (".concat(item[4], ") {").concat(item[1], "}");
          item[4] = supports;
        }
      }
      list.push(item);
    }
  };
  return list;
};

/***/ }),

/***/ "./node_modules/css-loader/dist/runtime/sourceMaps.js":
/*!************************************************************!*\
  !*** ./node_modules/css-loader/dist/runtime/sourceMaps.js ***!
  \************************************************************/
/***/ ((module) => {



module.exports = function (item) {
  var content = item[1];
  var cssMapping = item[3];
  if (!cssMapping) {
    return content;
  }
  if (typeof btoa === "function") {
    var base64 = btoa(unescape(encodeURIComponent(JSON.stringify(cssMapping))));
    var data = "sourceMappingURL=data:application/json;charset=utf-8;base64,".concat(base64);
    var sourceMapping = "/*# ".concat(data, " */");
    return [content].concat([sourceMapping]).join("\n");
  }
  return [content].join("\n");
};

/***/ }),

/***/ "./node_modules/style-loader/dist/runtime/injectStylesIntoStyleTag.js":
/*!****************************************************************************!*\
  !*** ./node_modules/style-loader/dist/runtime/injectStylesIntoStyleTag.js ***!
  \****************************************************************************/
/***/ ((module) => {



var stylesInDOM = [];
function getIndexByIdentifier(identifier) {
  var result = -1;
  for (var i = 0; i < stylesInDOM.length; i++) {
    if (stylesInDOM[i].identifier === identifier) {
      result = i;
      break;
    }
  }
  return result;
}
function modulesToDom(list, options) {
  var idCountMap = {};
  var identifiers = [];
  for (var i = 0; i < list.length; i++) {
    var item = list[i];
    var id = options.base ? item[0] + options.base : item[0];
    var count = idCountMap[id] || 0;
    var identifier = "".concat(id, " ").concat(count);
    idCountMap[id] = count + 1;
    var indexByIdentifier = getIndexByIdentifier(identifier);
    var obj = {
      css: item[1],
      media: item[2],
      sourceMap: item[3],
      supports: item[4],
      layer: item[5]
    };
    if (indexByIdentifier !== -1) {
      stylesInDOM[indexByIdentifier].references++;
      stylesInDOM[indexByIdentifier].updater(obj);
    } else {
      var updater = addElementStyle(obj, options);
      options.byIndex = i;
      stylesInDOM.splice(i, 0, {
        identifier: identifier,
        updater: updater,
        references: 1
      });
    }
    identifiers.push(identifier);
  }
  return identifiers;
}
function addElementStyle(obj, options) {
  var api = options.domAPI(options);
  api.update(obj);
  var updater = function updater(newObj) {
    if (newObj) {
      if (newObj.css === obj.css && newObj.media === obj.media && newObj.sourceMap === obj.sourceMap && newObj.supports === obj.supports && newObj.layer === obj.layer) {
        return;
      }
      api.update(obj = newObj);
    } else {
      api.remove();
    }
  };
  return updater;
}
module.exports = function (list, options) {
  options = options || {};
  list = list || [];
  var lastIdentifiers = modulesToDom(list, options);
  return function update(newList) {
    newList = newList || [];
    for (var i = 0; i < lastIdentifiers.length; i++) {
      var identifier = lastIdentifiers[i];
      var index = getIndexByIdentifier(identifier);
      stylesInDOM[index].references--;
    }
    var newLastIdentifiers = modulesToDom(newList, options);
    for (var _i = 0; _i < lastIdentifiers.length; _i++) {
      var _identifier = lastIdentifiers[_i];
      var _index = getIndexByIdentifier(_identifier);
      if (stylesInDOM[_index].references === 0) {
        stylesInDOM[_index].updater();
        stylesInDOM.splice(_index, 1);
      }
    }
    lastIdentifiers = newLastIdentifiers;
  };
};

/***/ }),

/***/ "./node_modules/style-loader/dist/runtime/insertBySelector.js":
/*!********************************************************************!*\
  !*** ./node_modules/style-loader/dist/runtime/insertBySelector.js ***!
  \********************************************************************/
/***/ ((module) => {



var memo = {};

/* istanbul ignore next  */
function getTarget(target) {
  if (typeof memo[target] === "undefined") {
    var styleTarget = document.querySelector(target);

    // Special case to return head of iframe instead of iframe itself
    if (window.HTMLIFrameElement && styleTarget instanceof window.HTMLIFrameElement) {
      try {
        // This will throw an exception if access to iframe is blocked
        // due to cross-origin restrictions
        styleTarget = styleTarget.contentDocument.head;
      } catch (e) {
        // istanbul ignore next
        styleTarget = null;
      }
    }
    memo[target] = styleTarget;
  }
  return memo[target];
}

/* istanbul ignore next  */
function insertBySelector(insert, style) {
  var target = getTarget(insert);
  if (!target) {
    throw new Error("Couldn't find a style target. This probably means that the value for the 'insert' parameter is invalid.");
  }
  target.appendChild(style);
}
module.exports = insertBySelector;

/***/ }),

/***/ "./node_modules/style-loader/dist/runtime/insertStyleElement.js":
/*!**********************************************************************!*\
  !*** ./node_modules/style-loader/dist/runtime/insertStyleElement.js ***!
  \**********************************************************************/
/***/ ((module) => {



/* istanbul ignore next  */
function insertStyleElement(options) {
  var element = document.createElement("style");
  options.setAttributes(element, options.attributes);
  options.insert(element, options.options);
  return element;
}
module.exports = insertStyleElement;

/***/ }),

/***/ "./node_modules/style-loader/dist/runtime/setAttributesWithoutAttributes.js":
/*!**********************************************************************************!*\
  !*** ./node_modules/style-loader/dist/runtime/setAttributesWithoutAttributes.js ***!
  \**********************************************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {



/* istanbul ignore next  */
function setAttributesWithoutAttributes(styleElement) {
  var nonce =  true ? __webpack_require__.nc : 0;
  if (nonce) {
    styleElement.setAttribute("nonce", nonce);
  }
}
module.exports = setAttributesWithoutAttributes;

/***/ }),

/***/ "./node_modules/style-loader/dist/runtime/styleDomAPI.js":
/*!***************************************************************!*\
  !*** ./node_modules/style-loader/dist/runtime/styleDomAPI.js ***!
  \***************************************************************/
/***/ ((module) => {



/* istanbul ignore next  */
function apply(styleElement, options, obj) {
  var css = "";
  if (obj.supports) {
    css += "@supports (".concat(obj.supports, ") {");
  }
  if (obj.media) {
    css += "@media ".concat(obj.media, " {");
  }
  var needLayer = typeof obj.layer !== "undefined";
  if (needLayer) {
    css += "@layer".concat(obj.layer.length > 0 ? " ".concat(obj.layer) : "", " {");
  }
  css += obj.css;
  if (needLayer) {
    css += "}";
  }
  if (obj.media) {
    css += "}";
  }
  if (obj.supports) {
    css += "}";
  }
  var sourceMap = obj.sourceMap;
  if (sourceMap && typeof btoa !== "undefined") {
    css += "\n/*# sourceMappingURL=data:application/json;base64,".concat(btoa(unescape(encodeURIComponent(JSON.stringify(sourceMap)))), " */");
  }

  // For old IE
  /* istanbul ignore if  */
  options.styleTagTransform(css, styleElement, options.options);
}
function removeStyleElement(styleElement) {
  // istanbul ignore if
  if (styleElement.parentNode === null) {
    return false;
  }
  styleElement.parentNode.removeChild(styleElement);
}

/* istanbul ignore next  */
function domAPI(options) {
  if (typeof document === "undefined") {
    return {
      update: function update() {},
      remove: function remove() {}
    };
  }
  var styleElement = options.insertStyleElement(options);
  return {
    update: function update(obj) {
      apply(styleElement, options, obj);
    },
    remove: function remove() {
      removeStyleElement(styleElement);
    }
  };
}
module.exports = domAPI;

/***/ }),

/***/ "./node_modules/style-loader/dist/runtime/styleTagTransform.js":
/*!*********************************************************************!*\
  !*** ./node_modules/style-loader/dist/runtime/styleTagTransform.js ***!
  \*********************************************************************/
/***/ ((module) => {



/* istanbul ignore next  */
function styleTagTransform(css, styleElement) {
  if (styleElement.styleSheet) {
    styleElement.styleSheet.cssText = css;
  } else {
    while (styleElement.firstChild) {
      styleElement.removeChild(styleElement.firstChild);
    }
    styleElement.appendChild(document.createTextNode(css));
  }
}
module.exports = styleTagTransform;

/***/ }),

/***/ "./style/index.css":
/*!*************************!*\
  !*** ./style/index.css ***!
  \*************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   "default": () => (__WEBPACK_DEFAULT_EXPORT__)
/* harmony export */ });
/* harmony import */ var _node_modules_style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! !../node_modules/style-loader/dist/runtime/injectStylesIntoStyleTag.js */ "./node_modules/style-loader/dist/runtime/injectStylesIntoStyleTag.js");
/* harmony import */ var _node_modules_style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_node_modules_style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _node_modules_style_loader_dist_runtime_styleDomAPI_js__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! !../node_modules/style-loader/dist/runtime/styleDomAPI.js */ "./node_modules/style-loader/dist/runtime/styleDomAPI.js");
/* harmony import */ var _node_modules_style_loader_dist_runtime_styleDomAPI_js__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(_node_modules_style_loader_dist_runtime_styleDomAPI_js__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _node_modules_style_loader_dist_runtime_insertBySelector_js__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! !../node_modules/style-loader/dist/runtime/insertBySelector.js */ "./node_modules/style-loader/dist/runtime/insertBySelector.js");
/* harmony import */ var _node_modules_style_loader_dist_runtime_insertBySelector_js__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(_node_modules_style_loader_dist_runtime_insertBySelector_js__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _node_modules_style_loader_dist_runtime_setAttributesWithoutAttributes_js__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! !../node_modules/style-loader/dist/runtime/setAttributesWithoutAttributes.js */ "./node_modules/style-loader/dist/runtime/setAttributesWithoutAttributes.js");
/* harmony import */ var _node_modules_style_loader_dist_runtime_setAttributesWithoutAttributes_js__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(_node_modules_style_loader_dist_runtime_setAttributesWithoutAttributes_js__WEBPACK_IMPORTED_MODULE_3__);
/* harmony import */ var _node_modules_style_loader_dist_runtime_insertStyleElement_js__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! !../node_modules/style-loader/dist/runtime/insertStyleElement.js */ "./node_modules/style-loader/dist/runtime/insertStyleElement.js");
/* harmony import */ var _node_modules_style_loader_dist_runtime_insertStyleElement_js__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(_node_modules_style_loader_dist_runtime_insertStyleElement_js__WEBPACK_IMPORTED_MODULE_4__);
/* harmony import */ var _node_modules_style_loader_dist_runtime_styleTagTransform_js__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! !../node_modules/style-loader/dist/runtime/styleTagTransform.js */ "./node_modules/style-loader/dist/runtime/styleTagTransform.js");
/* harmony import */ var _node_modules_style_loader_dist_runtime_styleTagTransform_js__WEBPACK_IMPORTED_MODULE_5___default = /*#__PURE__*/__webpack_require__.n(_node_modules_style_loader_dist_runtime_styleTagTransform_js__WEBPACK_IMPORTED_MODULE_5__);
/* harmony import */ var _node_modules_css_loader_dist_cjs_js_index_css__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! !!../node_modules/css-loader/dist/cjs.js!./index.css */ "./node_modules/css-loader/dist/cjs.js!./style/index.css");

      
      
      
      
      
      
      
      
      

var options = {};

options.styleTagTransform = (_node_modules_style_loader_dist_runtime_styleTagTransform_js__WEBPACK_IMPORTED_MODULE_5___default());
options.setAttributes = (_node_modules_style_loader_dist_runtime_setAttributesWithoutAttributes_js__WEBPACK_IMPORTED_MODULE_3___default());

      options.insert = _node_modules_style_loader_dist_runtime_insertBySelector_js__WEBPACK_IMPORTED_MODULE_2___default().bind(null, "head");
    
options.domAPI = (_node_modules_style_loader_dist_runtime_styleDomAPI_js__WEBPACK_IMPORTED_MODULE_1___default());
options.insertStyleElement = (_node_modules_style_loader_dist_runtime_insertStyleElement_js__WEBPACK_IMPORTED_MODULE_4___default());

var update = _node_modules_style_loader_dist_runtime_injectStylesIntoStyleTag_js__WEBPACK_IMPORTED_MODULE_0___default()(_node_modules_css_loader_dist_cjs_js_index_css__WEBPACK_IMPORTED_MODULE_6__["default"], options);




       /* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (_node_modules_css_loader_dist_cjs_js_index_css__WEBPACK_IMPORTED_MODULE_6__["default"] && _node_modules_css_loader_dist_cjs_js_index_css__WEBPACK_IMPORTED_MODULE_6__["default"].locals ? _node_modules_css_loader_dist_cjs_js_index_css__WEBPACK_IMPORTED_MODULE_6__["default"].locals : undefined);


/***/ })

}]);
//# sourceMappingURL=lib_index_js.b2f76b5c3fc6a9fbb9ff.js.map