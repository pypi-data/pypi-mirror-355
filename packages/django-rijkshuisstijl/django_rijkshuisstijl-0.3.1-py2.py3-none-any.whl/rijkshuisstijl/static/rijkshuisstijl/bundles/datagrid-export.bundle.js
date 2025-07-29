"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["datagrid-export"],{

/***/ "./rijkshuisstijl/js/components/datagrid/datagrid-export.js":
/*!******************************************************************!*\
  !*** ./rijkshuisstijl/js/components/datagrid/datagrid-export.js ***!
  \******************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/datagrid/constants.js");
/* harmony import */ var _form_constants__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ../form/constants */ "./rijkshuisstijl/js/components/form/constants.js");
/* harmony import */ var _toggle_constants__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ../toggle/constants */ "./rijkshuisstijl/js/components/toggle/constants.js");
const MAX_ITERATION_COUNT=100;/**
 * Makes sure data grid export buttons default to current page selection.
 */class DataGridExportHelper{/**
     * Constructor method.
     * @param {HTMLElement} node
     */constructor(node){/** @type {HTMLElement} */this.node=node;this.bindEvents();}/**
     * Binds events to callbacks.
     */bindEvents(){this.node.addEventListener('click',this.update.bind(this));}getDataGrid(){let node=this.node;let i=0;while(!node.classList.contains(_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_DATAGRID)){i++;node=node.parentNode;if(i>MAX_ITERATION_COUNT){throw`MAX_ITERATION_COUNT (${MAX_ITERATION_COUNT}) reached while trying to find data grid element.`;}}return node;}/**
     * Checks all checkboxes in the data grid if none has been checked.
     * @param {MouseEvent} e
     */update(e){const dataGrid=this.getDataGrid();const checkboxCells=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNodes(dataGrid,_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_DATAGRID,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_CELL,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_CHECKBOX);const checkboxesInputs=[...checkboxCells].map(node=>bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(node,_form_constants__WEBPACK_IMPORTED_MODULE_2__.BLOCK_INPUT));const selectedCheckboxInputs=checkboxesInputs.find(node=>node.checked);// Only check checkboxes if none hase been already checked.
if(!selectedCheckboxInputs){e.preventDefault();const form=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(dataGrid,_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_DATAGRID,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_FORM,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_ACTION);const selectAll=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(dataGrid,_toggle_constants__WEBPACK_IMPORTED_MODULE_3__.BLOCK_SELECT_ALL);// Select all checkboxes, including the "select all" toggle.
selectAll.checked=true;checkboxesInputs.forEach(node=>{node.checked=true;});const hiddenInput=document.createElement('input');hiddenInput.name=this.node.name;hiddenInput.value=this.node.value;hiddenInput.type='hidden';form.appendChild(hiddenInput);form.submit();}}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_1__.DATAGRID_EXPORTS].forEach(node=>new DataGridExportHelper(node));

/***/ })

}]);