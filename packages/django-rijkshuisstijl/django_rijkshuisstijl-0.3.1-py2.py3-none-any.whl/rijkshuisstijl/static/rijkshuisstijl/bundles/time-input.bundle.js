"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["time-input"],{

/***/ "./rijkshuisstijl/js/components/form/time-input.js":
/*!*********************************************************!*\
  !*** ./rijkshuisstijl/js/components/form/time-input.js ***!
  \*********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony import */ var flatpickr__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! flatpickr */ "./node_modules/flatpickr/dist/esm/index.js");
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/form/constants.js");
/**
 * Adds a timepicker to time inputs.
 * @class
 */class TimeInput{/**
     * Constructor method.
     * @param {HTMLInputElement} node
     */constructor(node){/** @type {HTMLInputElement} */this.node=node;this.update();}/**
     * Returns the placeholder string to use.
     * @return {string}
     */getPlaceholderFormat(){return this.isTime()?'00:00':'';}/**
     * Returns whether this.node is a time input.
     * @return bBoolean}
     */isTime(){return this.node.type==='time';}/**
     * Updates the placholder (if any) with the format returned by this.getPlaceholderFormat().
     */updatePlaceholder(){if(!this.node.placeholder){const placeholder=this.getPlaceholderFormat();this.node.placeholder=placeholder;}}/**
     * Adds the timepicker.
     */update(){this.updatePlaceholder();(0,flatpickr__WEBPACK_IMPORTED_MODULE_0__["default"])(this.node,{enableTime:true,noCalendar:true,time_24hr:true});}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_1__.TIME_INPUTS].forEach(node=>new TimeInput(node));

/***/ })

}]);