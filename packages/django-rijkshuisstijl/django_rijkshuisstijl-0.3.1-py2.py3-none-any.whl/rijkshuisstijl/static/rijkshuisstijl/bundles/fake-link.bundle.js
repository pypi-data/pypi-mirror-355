"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["fake-link"],{

/***/ "./rijkshuisstijl/js/components/fake-link/fake-link.js":
/*!*************************************************************!*\
  !*** ./rijkshuisstijl/js/components/fake-link/fake-link.js ***!
  \*************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   FakeLink: function() { return /* binding */ FakeLink; }
/* harmony export */ });
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/fake-link/constants.js");
/**
 * Class for fake (simulated) links.
 *
 * Toggle should have BLOCK_FAKE_LINK present in classList for detection.
 * Toggle should have data-href set to target location.
 * @class
 */class FakeLink{/**
     * Constructor method.
     * @param {HTMLElement} node
     */constructor(node){/** @type {HTMLElement} */this.node=node;/** @type {string} */this.href=this.node.dataset.href;this.bindEvents();}/**
     * Binds events to callbacks.
     */bindEvents(){if(bem_js__WEBPACK_IMPORTED_MODULE_0___default().hasModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_DOUBLE_CLICK)){this.node.addEventListener('dblclick',this.navigate.bind(this));}else{this.node.addEventListener('click',this.navigate.bind(this));}}/**
     * Navigates to this.href.
     */navigate(){window.location=this.href;}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_1__.FAKE_LINKS].forEach(node=>new FakeLink(node));

/***/ })

}]);