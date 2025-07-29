"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["datagrid-edit"],{

/***/ "./rijkshuisstijl/js/components/datagrid/datagrid-edit.js":
/*!****************************************************************!*\
  !*** ./rijkshuisstijl/js/components/datagrid/datagrid-edit.js ***!
  \****************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/datagrid/constants.js");
class DataGridEdit{/**
     * Constructor method.
     * @param {HTMLElement} node
     */constructor(node){/** @type {HTMLElement} */this.node=node;this.bindEvents();}/**
     * Binds events to callbacks.
     */bindEvents(){this.node.addEventListener('rh-toggle',this.update.bind(this));}/**
     * Toggle MODIFIER_EDIT on this.node based on presense of datagrid__row--edit matches.
     */update(){const editable_row=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNodes(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_DATAGRID,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_ROW,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_EDIT);const exp=Boolean(editable_row.length);bem_js__WEBPACK_IMPORTED_MODULE_0___default().toggleModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_EDIT,exp);}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_1__.DATAGRIDS].forEach(node=>new DataGridEdit(node));

/***/ })

}]);