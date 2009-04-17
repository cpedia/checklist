YAHOO.namespace("checklist");
YAHOO.namespace("checklist.columns");
YAHOO.namespace("checklist.templates");
YAHOO.namespace("checklist.templates.columns");
YAHOO.namespace("checklist.items");

String.prototype.trim = function () {
    return this.replace(/^[\s\,]*/, "").replace(/[\s\,]*$/, ""); //for remove the space and comma at the begining/end of the tag.
};

var init_input_default_value = function init_input(id) {
    var inp = document.getElementById(id).getElementsByTagName('input');
    for (var i = 0; i < inp.length; i++) {
        if (inp[i].type == 'text' || inp[i].type =="textarea") {
            inp[i].setAttribute("rel", inp[i].defaultValue)
            inp[i].onfocus = function() {
                if (this.value == this.getAttribute("rel")) {
                    this.value = "";
                } else {
                    this.select();
                }
            }
            inp[i].onblur = function() {
                if (this.value == "") {
                    this.value = this.getAttribute("rel");
                }
            }
        }
    }
};
