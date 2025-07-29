"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["paginator"],{

/***/ "./rijkshuisstijl/js/components/paginator/paginator.js":
/*!*************************************************************!*\
  !*** ./rijkshuisstijl/js/components/paginator/paginator.js ***!
  \*************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Paginator: function() { return /* binding */ Paginator; }
/* harmony export */ });
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var urijs__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! urijs */ "./node_modules/urijs/src/URI.js");
/* harmony import */ var urijs__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(urijs__WEBPACK_IMPORTED_MODULE_1__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/paginator/constants.js");
/**
 * Contains logic for making the paginator work with existing GET params.
 * @class
 */class Paginator{/**
     * Constructor method.
     * @param {HTMLFormElement} node
     */constructor(node){/** @type {HTMLFormElement} */this.node=node;/** @type {HTMLInputElement} */this.input=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(this.node,_constants__WEBPACK_IMPORTED_MODULE_2__.BLOCK_INPUT);this.bindEvents();}/**
     * Binds events to callbacks.
     */bindEvents(){this.node.addEventListener('submit',this.onChange.bind(this));this.node.addEventListener('change',this.onChange.bind(this));this.node.addEventListener('click',this.onClick.bind(this));}/**
     * Callback for change event on this.node.
     * @param {Event} e
     */onChange(e){e.preventDefault();this.navigate();}/**
     * Callback for click event on this.node.
     * @param {Event} e
     */onClick(e){e.preventDefault();if(e.target.dataset.page){this.navigate(e.target.dataset.page);}}/**
     * Navigate to the page specified in this.input.
     */navigate(){let page=arguments.length>0&&arguments[0]!==undefined?arguments[0]:this.input.value;window.location=urijs__WEBPACK_IMPORTED_MODULE_1___default()(window.location).setSearch(this.input.name,page);}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_2__.PAGINATORS].forEach(node=>new Paginator(node));

/***/ })

}]);