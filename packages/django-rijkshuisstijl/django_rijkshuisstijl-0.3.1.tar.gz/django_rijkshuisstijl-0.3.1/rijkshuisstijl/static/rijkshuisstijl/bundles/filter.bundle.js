"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["filter"],{

/***/ "./rijkshuisstijl/js/components/filter/filter.js":
/*!*******************************************************!*\
  !*** ./rijkshuisstijl/js/components/filter/filter.js ***!
  \*******************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Filter: function() { return /* binding */ Filter; }
/* harmony export */ });
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/filter/constants.js");
/**
 * Class for generic filters.
 * Filter should have MODIFIER_FILTER present in classList for detection.
 * Filter should have data-filter-target set to query selector for targets.
 * @class
 */class Filter{/**
     * Constructor method.
     * @param {HTMLElement} node
     */constructor(node){/** @type {HTMLElement} */this.node=node;/** @type {HTMLInputElement} */this.input=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_FILTER,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_INPUT);this.bindEvents();this.applyFilter();}/**
     * Binds events to callbacks.
     */bindEvents(){this.node.addEventListener('input',this.filter.bind(this));}/**
     * Applies/discard the filter based on this.input.value.
     */filter(){if(this.input.value){this.applyFilter();}else{this.discardFilter();}}/**
     * Hides all the nodes matching query selector set in data-filter-target that don't match this.input.value.
     */applyFilter(){setTimeout(()=>{let selection=document.querySelectorAll(this.node.dataset.filterTarget);let query=this.input.value.toUpperCase();[...selection].forEach(node=>{bem_js__WEBPACK_IMPORTED_MODULE_0___default().addModifier(node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_MATCH);bem_js__WEBPACK_IMPORTED_MODULE_0___default().removeModifier(node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_NO_MATCH);if(!bem_js__WEBPACK_IMPORTED_MODULE_0___default().hasModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_CLASS_ONLY)){node.style.removeProperty('display');}if(!node.textContent.toUpperCase().match(query)){bem_js__WEBPACK_IMPORTED_MODULE_0___default().removeModifier(node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_MATCH);bem_js__WEBPACK_IMPORTED_MODULE_0___default().addModifier(node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_NO_MATCH);if(!bem_js__WEBPACK_IMPORTED_MODULE_0___default().hasModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_CLASS_ONLY)){node.style.display='none';}}});});}/**
     * Removes display property from inline style of every node matching query selector set in data-filter-target.
     */discardFilter(){let selection=document.querySelectorAll(this.node.dataset.filterTarget);[...selection].forEach(node=>{if(!bem_js__WEBPACK_IMPORTED_MODULE_0___default().hasModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_CLASS_ONLY)){node.style.removeProperty('display');}bem_js__WEBPACK_IMPORTED_MODULE_0___default().removeModifier(node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_NO_MATCH);bem_js__WEBPACK_IMPORTED_MODULE_0___default().addModifier(node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_MATCH);});}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_1__.FILTERS].forEach(filter=>new Filter(filter));

/***/ })

}]);