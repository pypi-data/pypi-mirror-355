"use strict";
(self["webpackChunkdjango_rijkshuisstijl"] = self["webpackChunkdjango_rijkshuisstijl"] || []).push([["tabs"],{

/***/ "./rijkshuisstijl/js/components/tabs/tabs.js":
/*!***************************************************!*\
  !*** ./rijkshuisstijl/js/components/tabs/tabs.js ***!
  \***************************************************/
/***/ (function(__unused_webpack_module, __webpack_exports__, __webpack_require__) {

__webpack_require__.r(__webpack_exports__);
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! bem.js */ "./node_modules/bem.js/dist/bem.js");
/* harmony import */ var bem_js__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(bem_js__WEBPACK_IMPORTED_MODULE_0__);
/* harmony import */ var _constants__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./constants */ "./rijkshuisstijl/js/components/tabs/constants.js");
/**
 * Contains logic for tabs.
 * @class
 */class Tabs{/**
     * Constructor method.
     * @param {HTMLElement} node
     */constructor(node){/** @type {HTMLElement} */this.node=node;/** @type {NodeList} */this.listItems=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNodes(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_TABS,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_LIST_ITEM);/** @type {NodeList} */this.links=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNodes(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_TABS,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_LINK);/** @type {NodeList} */this.track=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNode(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_TABS,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_TRACK);/** @type {NodeList} */this.tabs=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getChildBEMNodes(this.node,_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_TABS,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_TAB);this.bindEvents();if(!this.activateHashLinkTab()){this.activateCurrentTab();}}/**
     * Binds events to callbacks.
     */bindEvents(){[...this.links].forEach(link=>this.bindLink(link));window.addEventListener('popstate',this.activateHashLinkTab.bind(this));window.addEventListener('resize',this.activateCurrentTab.bind(this));}/**
     * Binds link click to callback.
     * @param {HTMLAnchorElement} link
     */bindLink(link){link.addEventListener('click',this.onClick.bind(this));}/**
     * (Re)activates the active tab, or the first tab.
     */activateCurrentTab(){let id=this.getActiveTabId();if(id){this.activateTab(id);}}/**
     * (Re)activates the active tab, or the first tab.
     */activateHashLinkTab(){const id=window.location.hash.replace('#','');const node=document.getElementById(id);if(node&&node.classList.contains(bem_js__WEBPACK_IMPORTED_MODULE_0___default().getBEMClassName(_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_TABS,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_TAB))){const listener=()=>{window.scrollTo(0,0);window.removeEventListener('scroll',listener);};window.addEventListener('scroll',listener);this.activateTab(id);return true;}}/**
     * Returns the active tab id (this.node.dataset.tabId) or the first tab's id.
     * @returns {(string|void)}
     */getActiveTabId(){let tabId=this.node.dataset.tabId;if(tabId){return tabId;}else{try{return this.tabs[0].id;}catch(e){}}}/**
     * Handles link click event.
     * @param {MouseEvent} e
     */onClick(e){e.preventDefault();let link=e.target;let id=link.attributes.href.value.replace('#','');history.pushState({},document.title,link);this.activateTab(id);}/**
     * Activates tab with id.
     * @param {string} id The id of the tab.
     * @return {HTMLElement}
     */activateTab(id){let link=[...this.links].find(link=>link.attributes.href.value==='#'+id);let listItem=this.getListItemByLink(link);let tabIndex=[...this.tabs].findIndex(tab=>tab.id===id);let tab=this.tabs[tabIndex];[...this.listItems,...this.tabs].forEach(node=>bem_js__WEBPACK_IMPORTED_MODULE_0___default().removeModifier(node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_ACTIVE));[listItem,tab].forEach(node=>bem_js__WEBPACK_IMPORTED_MODULE_0___default().addModifier(node,_constants__WEBPACK_IMPORTED_MODULE_1__.MODIFIER_ACTIVE));this.node.dataset.tabId=id;// Support leaflet.
//
// Leaflet won't render correctly if not visible. Therefore, we need to invalidate it's size to re-render it.
// We don't have a direct reference to the leaflet instances so we try to find the callbacks in
// window._leaflet_events, then call it when activating the tab (if the even name matches resize).
//
// FIXME: There is probably a better way to do this.
try{Object.entries(window._leaflet_events).forEach(_ref=>{let[event_name,callback]=_ref;if(event_name.indexOf('resize')>-1){callback();}});}catch(e){}}/**
     * Finds the list item containing link up the DOM tree.
     * @param {HTMLAnchorElement} link
     */getListItemByLink(link){let listItemClassName=bem_js__WEBPACK_IMPORTED_MODULE_0___default().getBEMClassName(_constants__WEBPACK_IMPORTED_MODULE_1__.BLOCK_TABS,_constants__WEBPACK_IMPORTED_MODULE_1__.ELEMENT_LIST_ITEM);let i=0;while(!link.classList.contains(listItemClassName)){link=link.parentElement;if(i>100){console.error('Failed to find list item');break;}}return link;}}// Start!
[..._constants__WEBPACK_IMPORTED_MODULE_1__.TABS].forEach(tabs=>new Tabs(tabs));

/***/ })

}]);