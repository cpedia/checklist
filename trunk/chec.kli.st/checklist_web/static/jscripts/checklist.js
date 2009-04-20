YAHOO.namespace("checklist");
YAHOO.namespace("checklist.columns");
YAHOO.namespace("checklist.templates");
YAHOO.namespace("checklist.templates.columns");
YAHOO.namespace("checklist.items");

String.prototype.trim = function () {
    return this.replace(/^[\s\,]*/, "").replace(/[\s\,]*$/, ""); //for remove the space and comma at the begining/end of the tag.
};

var init_input_default_value = function init_input(elements) {
    if(!YAHOO.lang.isArray(elements)){
       elements = [elements];
    }
    for (var i = 0; i < elements.length; i++) {
            var e = elements[i];
            if(typeof e === 'string'){
                e = document.getElementById(e);
            }
            e.setAttribute("rel", e.defaultValue);
            e.onfocus = function() {
                if (this.value == this.getAttribute("rel")) {
                    this.value = "";
                } else {
                    this.select();
                }
            };
            e.onblur = function() {
                if (this.value == "") {
                    this.value = this.getAttribute("rel");
                }
            };
    }
};
