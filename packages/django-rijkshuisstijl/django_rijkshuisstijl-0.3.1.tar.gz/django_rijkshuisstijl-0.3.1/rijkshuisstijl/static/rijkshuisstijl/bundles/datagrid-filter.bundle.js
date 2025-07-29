"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["datagrid-filter"],{

/***/ "./rijkshuisstijl/js/components/datagrid/datagrid-filter.js":
/*!******************************************************************!*\
  !*** ./rijkshuisstijl/js/components/datagrid/datagrid-filter.js ***!
  \******************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/datagrid/constants.js");
/* harmony import */ var _form_constants__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../form/constants */ "./rijkshuisstijl/js/components/form/constants.js");
/**
 * Polyfills form association from datagrid filter.
 */class DataGridFilter{/**
     * Constructor method.
     * @param {HTMLElement} node
     */constructor(node){/** @type {HTMLElement} */this.node=node;/** @type {(HTMLFormElement|null)} */this.form=this.getForm();/** @type {(HTMLInputElement|HTMLSelectElement|null)} */this.input=this.getInput();this.bindEvents();}/**
     * Binds events to callbacks.
     */bindEvents(){if(this.input){this.input.addEventListener('change',this.onSubmit.bind(this));}}/**
     * Finds the form associated with the filter.
     * @return {(HTMLFormElement|null)}
     */getForm(){const input=this.getInput();if(input){if(!input.form){const formId=input.getAttribute('form');return document.getElementById(formId);}return input.form;}}/**
     * Finds the first input or select as child of this.node.
     * @return {(HTMLInputElement|HTMLSelectElement|null)}
     */getInput(){const input=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(this.node,_form_constants__WEBPACK_IMPORTED_MODULE_2__.BLOCK_INPUT);const select=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(this.node,_form_constants__WEBPACK_IMPORTED_MODULE_2__.BLOCK_SELECT);return input||select;}/**
     * Appends clone of inputs pointing to this.form before submitting it when browser does not support input form
     * attribute.
     */onSubmit(){const formId=this.form.id;const inputs=document.querySelectorAll(`[form="${formId}"]`);[...inputs].forEach(node=>{const newNode=document.createElement('input');if(node.form){// Browser supports input form attribute.
return;}newNode.name=node.name;newNode.type='hidden';newNode.value=node.value;this.form.appendChild(newNode);});this.form.submit();}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_1__.DATAGRID_FILTERS].forEach(node=>new DataGridFilter(node));

/***/ })

}]);