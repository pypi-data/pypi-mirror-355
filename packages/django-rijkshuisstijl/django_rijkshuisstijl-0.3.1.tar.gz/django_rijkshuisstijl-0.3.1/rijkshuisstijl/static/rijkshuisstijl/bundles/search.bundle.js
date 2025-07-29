"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["search"],{

/***/ "./rijkshuisstijl/js/components/button/constants.js":
/*!**********************************************************!*\
  !*** ./rijkshuisstijl/js/components/button/constants.js ***!
  \**********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   BLOCK_BUTTON: function() { return /* binding */ BLOCK_BUTTON; },
/* harmony export */   MODIFIER_PRIMARY: function() { return /* binding */ MODIFIER_PRIMARY; },
/* harmony export */   MODIFIER_SECONDARY: function() { return /* binding */ MODIFIER_SECONDARY; }
/* harmony export */ });
/** @const {string} */const BLOCK_BUTTON='button';/** @const {string} Modifier indicating a primary button. */const MODIFIER_PRIMARY='primary';/** @const {string} Modifier indicating a secondary button. */const MODIFIER_SECONDARY='secondary';

/***/ }),

/***/ "./rijkshuisstijl/js/components/search/search.js":
/*!*******************************************************!*\
  !*** ./rijkshuisstijl/js/components/search/search.js ***!
  \*******************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   Search: function() { return /* binding */ Search; }
/* harmony export */ });
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _button_constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ../button/constants */ "./rijkshuisstijl/js/components/button/constants.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/search/constants.js");
/**
 * Contains additional logic controlling search widget.
 * NOTE: Open/close behaviour controlled by button (ToggleButton).
 * @class
 */class Search{/**
     * Constructor method.
     * @param {HTMLFormElement} node
     */constructor(node){/** @type {HTMLFormElement} */this.node=node;/** @type {HTMLInputElement} */this.input=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(this.node,_constants__WEBPACK_IMPORTED_MODULE_2__.BLOCK_SEARCH,_constants__WEBPACK_IMPORTED_MODULE_2__.ELEMENT_INPUT);/** @type {HTMLButtonElement} */this.buttonPrimary=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(this.node,_button_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_BUTTON,false,_button_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_PRIMARY);/** @type {HTMLButtonElement} */this.buttonSecondary=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(this.node,_button_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_BUTTON,false,_button_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_SECONDARY);this.bindEvents();}/**
     * Binds events to callbacks.
     */bindEvents(){this.buttonPrimary.addEventListener('click',this.onClickButtonPrimary.bind(this));this.buttonSecondary.addEventListener('click',this.onClickButtonSecondary.bind(this));this.input.addEventListener('blur',this.onBlur.bind(this));this.input.addEventListener('keypress',this.onPressEnter.bind(this));}/**
     * Callback for keypress event on focused input.
     * Submits for if the user pressed enter and there is an input value.
     */onPressEnter(e){const keyCode=e.keyCode;if(keyCode===13){e.preventDefault();if(this.input.value){this.input.form.submit();}}}/**
     * Callback for click event on this.buttonPrimary.
     * Submits form if input has value.
     * Focuses this.input if MODIFIER_OPEN is set on this.node.
     * Blurs this.input otherwise.
     */onClickButtonPrimary(){if(bem_js__WEBPACK_IMPORTED_MODULE_0___default().hasModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_2__.MODIFIER_OPEN)){if(this.input.value){this.input.form.submit();}this.input.focus();}else{this.input.blur();}}/**
     * Callback for click event on this.buttonSecondary.
     * Clears/focuses this.input.
     * @param {Event} e
     */onClickButtonSecondary(e){e.preventDefault();this.input.value='';this.input.focus();}/**
     * Callback for blur event on this.input.
     * Calls this.close() if input does not have value.
     * @param {Event} e
     */onBlur(e){if(!this.input.value&&!e.relatedTarget){this.close();}}/**
     * Additional control for removing MODIFIER_OPEN for this.node.
     * NOTE: Open/close behaviour controlled by button (ToggleButton).
     */close(){bem_js__WEBPACK_IMPORTED_MODULE_0___default().removeModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_2__.MODIFIER_OPEN);}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_2__.SEARCHES].forEach(search=>new Search(search));

/***/ })

}]);