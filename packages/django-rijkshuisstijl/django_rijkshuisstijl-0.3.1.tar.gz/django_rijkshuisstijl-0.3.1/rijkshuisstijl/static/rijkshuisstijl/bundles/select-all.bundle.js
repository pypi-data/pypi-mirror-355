"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["select-all"],{

/***/ "./rijkshuisstijl/js/components/toggle/select-all.js":
/*!***********************************************************!*\
  !*** ./rijkshuisstijl/js/components/toggle/select-all.js ***!
  \***********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony export */ __webpack_require__.d(__webpack_exports__, {
/* harmony export */   SelectAll: function() { return /* binding */ SelectAll; }
/* harmony export */ });
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/toggle/constants.js");
/**
 * Class for generic select all checkboxes.
 * Toggle should have BLOCK_SELECT_ALL present in classList for detection.
 * Toggle should have data-select-all set to queryselector for target(s).
 * @class
 */class SelectAll{/**
     * Constructor method.
     * @param {HTMLInputElement} node
     */constructor(node){/** @type {HTMLInputElement} */this.node=node;this.bindEvents();}/**
     * Binds events to callbacks.
     */bindEvents(){this.node.addEventListener('click',this.onClick.bind(this));}/**
     * Callback for this.node click.
     * @param {Event} e
     */onClick(e){e.stopPropagation();e.preventDefault();setTimeout(this.toggle.bind(this));}/**
     * Performs toggle.
     * @param {boolean} [exp] If passed, add/removes this.toggleModifier based on exp.
     */toggle(){let exp=arguments.length>0&&arguments[0]!==undefined?arguments[0]:!this.getState();this.getTargets().forEach(target=>{let event=document.createEvent('Event');event.initEvent('change',true,true);setTimeout(()=>target.dispatchEvent(event));target.checked=exp;});this.node.checked=exp;}/**
     * Returns the checkbox state.
     * @returns {boolean} Boolean
     */getState(){return this.node.checked;}/**
     * Returns all the targets for this.node.
     * @returns {*}
     */getTargets(){let targets=[];let selector=this.node.dataset.selectAll;selector.split(',').filter(selector=>selector.length).forEach(selector=>targets=[...targets,...document.querySelectorAll(selector)]);return targets;}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_0__.SELECT_ALLS].forEach(node=>new SelectAll(node));

/***/ })

}]);