$(function() {
    function ThingiverseSidebarViewModel(parameters) {
        var self = this;
        self.settings = parameters[0];
        self.thingid = ko.observable();
        self.downloadThing = function(url) {
          url = OctoPrint.getBlueprintUrl("thingiverse") + "download";
          console.log("testing");
          console.log(url+self.thingid());

          OctoPrint.postJson(url, {"thingid":self.thingid()})
            .done(function(response) {
              console.log(response);

            });

        };
    }

    function onDataUpdaterPluginMessage(plugin, message) {
        if (plugin=='thingiverse') {
        }        
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: ThingiverseSidebarViewModel,
        additionalNames: [],
        dependencies: [],
        optional: [],
        elements: ["#sidebar_plugin_thingiverse"]
    });
});
