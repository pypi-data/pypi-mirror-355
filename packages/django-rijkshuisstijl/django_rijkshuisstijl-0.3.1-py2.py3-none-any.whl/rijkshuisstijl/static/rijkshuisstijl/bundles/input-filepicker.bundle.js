"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["input-filepicker"],{

/***/ "./rijkshuisstijl/js/components/form/input-filepicker.js":
/*!***************************************************************!*\
  !*** ./rijkshuisstijl/js/components/form/input-filepicker.js ***!
  \***************************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/form/constants.js");
/**
 * Updates label on input file picker.
 * @class
 */class InputFilePicker{/**
     * Constructor method.
     * @param {HTMLLabelElement} node
     */constructor(node){/** @type {HTMLLabelElement} */this.node=node;/** @type {HTMLInputElement} */this.input=this.node.previousElementSibling;this.bindEvents();}/**
     * Returns the name of the selected file or an empty string.
     * @return {string}
     */getFileName(){if(this.input.files.length){return this.input.files[0].name;}return'';}/**
     * Binds events to callbacks.
     */bindEvents(){this.input.addEventListener('change',this.update.bind(this));}/**
     * Updates the textcontent of the input file picker with the input's selected file name.
     */update(){this.node.textContent=this.getFileName();}}// START!
[..._constants__WEBPACK_IMPORTED_MODULE_0__.INPUT_FILEPICKERS].forEach(node=>new InputFilePicker(node));

/***/ })

}]);