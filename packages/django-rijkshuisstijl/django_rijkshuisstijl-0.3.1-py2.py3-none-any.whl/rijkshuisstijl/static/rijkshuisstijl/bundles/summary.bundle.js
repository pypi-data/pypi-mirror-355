"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["summary"],{

/***/ "./rijkshuisstijl/js/components/summary/summary.js":
/*!*********************************************************!*\
  !*** ./rijkshuisstijl/js/components/summary/summary.js ***!
  \*********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/summary/constants.js");
/** @const {number} getKeyValue() while loop limit. */const MAX_ITERATION_COUNT=10;/**
 * Controls auto toggle inputs if not valid.
 * @class
 */class SummaryEdit{/**
     * Constructor method.
     * @param {HTMLElement} node
     */constructor(node){/** @type {HTMLElement} */this.node=node;/** @type {NodeList} Children of node that can be validated. */this.validatables=this.node.querySelectorAll(':invalid, :valid');this.bindEvents();}/**
     * Binds events to callbacks.
     */bindEvents(){[...this.validatables].forEach(node=>node.addEventListener('invalid',this.update.bind(this,node)));}/**
     * Finds the key value element associated with node.
     * @param {HTMLElement} node
     * @return {HTMLElement}
     */getKeyValue(node){let i=0;const className=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getBEMClassName(_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_SUMMARY,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_KEY_VALUE);while(!node.classList.contains(className)){i++;node=node.parentNode;if(i>MAX_ITERATION_COUNT){throw`MAX_ITERATION_COUNT (${MAX_ITERATION_COUNT}) reached while trying to find key value element.`;}}return node;}/**
     * Makes sure node is visible if not valid.
     * @param {HTMLElement} node
     */update(node){const toggle=this.getKeyValue(node);bem_js__WEBPACK_IMPORTED_MODULE_0___default().addModifier(toggle,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_EDIT);node.focus();node.scrollIntoView();}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_1__.SUMMARIES].forEach(node=>new SummaryEdit(node));

/***/ })

}]);