"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["select"],{

/***/ "./rijkshuisstijl/js/components/form/select.js":
/*!*****************************************************!*\
  !*** ./rijkshuisstijl/js/components/form/select.js ***!
  \*****************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Select: function() { return /* binding */ Select; }
/* harmony export */ });
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/form/constants.js");
/**
 * Detects whether a select has a value.
 * @class
 */class Select{/**
     * Constructor method.
     * @param {HTMLSelectElement} node
     */constructor(node){/** @type {HTMLSelectElement} */this.node=node;this.bindEvents();this.update();}/**
     * Binds events to callbacks.
     */bindEvents(){this.node.addEventListener('change',this.update.bind(this));}/**
     * Toggles MODIFIER_HAS_VALUE based on this.node.value.
     */update(){const exp=Boolean(''+this.node.value);bem_js__WEBPACK_IMPORTED_MODULE_0___default().toggleModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_HAS_VALUE,exp);}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_1__.SELECTS].forEach(node=>new Select(node));

/***/ })

}]);