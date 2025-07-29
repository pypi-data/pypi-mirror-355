(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["date-input"],{

/***/ "./node_modules/flatpickr/dist/l10n/nl.js":
/*!************************************************!*\
  !*** ./node_modules/flatpickr/dist/l10n/nl.js ***!
  \************************************************/
/***/ (function(__unused_webpack_module, exports) {

(function (global, factory) {
   true ? factory(exports) :
  0;
}(this, (function (exports) { 'use strict';

  var fp = typeof window !== "undefined" && window.flatpickr !== undefined
      ? window.flatpickr
      : {
          l10ns: {},
      };
  var Dutch = {
      weekdays: {
          shorthand: ["zo", "ma", "di", "wo", "do", "vr", "za"],
          longhand: [
              "zondag",
              "maandag",
              "dinsdag",
              "woensdag",
              "donderdag",
              "vrijdag",
              "zaterdag",
          ],
      },
      months: {
          shorthand: [
              "jan",
              "feb",
              "mrt",
              "apr",
              "mei",
              "jun",
              "jul",
              "aug",
              "sept",
              "okt",
              "nov",
              "dec",
          ],
          longhand: [
              "januari",
              "februari",
              "maart",
              "april",
              "mei",
              "juni",
              "juli",
              "augustus",
              "september",
              "oktober",
              "november",
              "december",
          ],
      },
      firstDayOfWeek: 1,
      weekAbbreviation: "wk",
      rangeSeparator: " t/m ",
      scrollTitle: "Scroll voor volgende / vorige",
      toggleTitle: "Klik om te wisselen",
      time_24hr: true,
      ordinal: function (nth) {
          if (nth === 1 || nth === 8 || nth >= 20)
              return "ste";
          return "de";
      },
  };
  fp.l10ns.nl = Dutch;
  var nl = fp.l10ns;

  exports.Dutch = Dutch;
  exports.default = nl;

  Object.defineProperty(exports, '__esModule', { value: true });

})));


/***/ }),

/***/ "./rijkshuisstijl/js/components/form/date-input.js":
/*!*********************************************************!*\
  !*** ./rijkshuisstijl/js/components/form/date-input.js ***!
  \*********************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

"use strict";
__webpack_require__.r(__webpack_exports__);
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var flatpickr__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! flatpickr */ "./node_modules/flatpickr/dist/esm/index.js");
/* harmony import */ var flatpickr_dist_l10n_nl__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! flatpickr/dist/l10n/nl */ "./node_modules/flatpickr/dist/l10n/nl.js");
/* harmony import */ var flatpickr_dist_l10n_nl__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(flatpickr_dist_l10n_nl__WEBPACK_IMPORTED_MODULE_2__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/form/constants.js");
/**
 * Adds a datepicker to date inputs.
 * @class
 */class DateInput{/**
     * Constructor method.
     * @param {HTMLInputElement} node
     */constructor(node){/** @type {HTMLInputElement} */this.node=node;this.update();}/**
     * Returns the date format to use with the datepicker.
     * @return {string}
     */getDateFormat(){if(this.node.dataset.dateFormat){return this.node.dataset.dateFormat;}return this.isDateTime()?'d-m-Y H:1':'d-m-Y';}/**
     * Returns the (Dutch) locale to use.
     * @return {CustomLocale}
     */getLocale(){const locale=flatpickr_dist_l10n_nl__WEBPACK_IMPORTED_MODULE_2__.Dutch;locale.firstDayOfWeek=1;// Start on monday.
return locale;}/**
     * Returns the mode to use, either "range" or "single".
     * @return {string}
     */getMode(){return bem_js__WEBPACK_IMPORTED_MODULE_0___default().hasModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_3__.MODIFIER_DATE_RANGE)?'range':'single';}/**
     * @TODO: Yet to be supported.
     * @return {boolean}
     */isDateTime(){return this.node.type==='datetime';}/**
     * onReady callback for flatpickr.
     * @param {Array} selectedDates
     * @param {string} dateStr
     * @param {Object} flatpickr
     */onReady(selectedDates,dateStr,flatpickr){this.copyAttrs(flatpickr.altInput);this.cleanValue();}/**
     * Copies attributes of this.node to target only if not already set on target.
     * @param {HTMLElement} target
     */copyAttrs(target){const targetAttributes=target.attributes;const excludedAttributes=['form','name','value'];[...this.node.attributes].forEach(attr=>{if(!(attr.name in targetAttributes)&&excludedAttributes.indexOf(attr.name)===-1){target.setAttribute(attr.name,attr.value);}});}/**
     * Makes sure a useful value is set on the value attribute.
     */cleanValue(){if(!this.node.value.match(/\d/)){this.node.value='';}}/**
     * Adds MODIFIER_DATE to this.node.
     */updateClassName(){bem_js__WEBPACK_IMPORTED_MODULE_0___default().addModifier(this.node,_constants__WEBPACK_IMPORTED_MODULE_3__.MODIFIER_DATE);}/**
     * Adds placeholder to this.node.
     */updatePlaceholder(){if(!this.node.placeholder){const placeholder=this.getDateFormat().replace('d','dd').replace('m','mm').replace('Y','yyyy');this.node.placeholder=placeholder;}}/**
     * Adds the datepicker.
     */update(){this.updateClassName();this.updatePlaceholder();const flatPicker=(0,flatpickr__WEBPACK_IMPORTED_MODULE_1__["default"])(this.node,{allowInput:true,altInput:true,altInputClass:this.node.className,altFormat:this.getDateFormat(),dateFormat:'Y-m-d',defaultDate:this.node.value.split('/'),locale:this.getLocale(),mode:this.getMode(),onReady:this.onReady.bind(this)});flatPicker.l10n.rangeSeparator='/';}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_3__.DATE_INPUTS,..._constants__WEBPACK_IMPORTED_MODULE_3__.DATE_RANGE_INPUTS].forEach(node=>new DateInput(node));

/***/ })

}]);