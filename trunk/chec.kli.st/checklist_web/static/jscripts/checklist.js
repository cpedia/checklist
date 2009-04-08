YAHOO.namespace("checklist");
YAHOO.namespace("checklist.columns");
YAHOO.namespace("checklist.templates");
YAHOO.namespace("checklist.templates.columns");

String.prototype.trim = function () {
    return this.replace(/^[\s\,]*/, "").replace(/[\s\,]*$/, ""); //for remove the space and comma at the begining/end of the tag.
};

