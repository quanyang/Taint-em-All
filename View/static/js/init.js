(function($){
  function updateStats(time,numOfSinks) {
    $('.stats').html("");
    $('.stats').append(`Time Taken: ${time}s</br>`);
    $('.stats').append(`No. of Tainted Sinks: ${numOfSinks}</br>`);
  }
  function showModules(profile,data) {
    $('.module-select').html("");
    var index = 0;
    profile.forEach(function(traversal) {
      traversalName = traversal.traversal;
      $('.module-select').append(`<li class="collection-header" style="border-bottom:0px;"><h7>${traversalName}</h7></li>`);
      $('.module-select').append(`<li class="collection-item" style="display:inline-block;border-top:0px;padding-right:0px;">--></li>`);
      var moduleIndex = 0;
      traversal.modules.forEach(function(module) {
        $('.module-select').append(`<li class="collection-item module-item" data-traversal="${index}" data-module="${moduleIndex}" style="display:inline-block">${module[1]}</li>`);
        moduleIndex++;
      });
      index++;
      $('.module-select').show();
      $('.module-item').click(function (event) {
        $('.module-item').removeClass('active');
        $(this).addClass('active');
        updateColorState(data.stats[event.currentTarget.getAttribute('data-traversal')][event.currentTarget.getAttribute('data-module')]);
      });
    });
  }

  $(function(){
    $('.delete-traversal').click(function (event) {
      $.post("/updateProfile", {"profileName": profileName, "traversal": event.currentTarget.id, "delete":true},
             function (data) {
              location.reload();
            });
    });

    $('.delete-module').click(function(event) {
      traversal = event.currentTarget.parentElement.parentElement.parentElement.id;
      module = event.currentTarget.id;
      $.post("/updateProfile", {"profileName": profileName, "traversal": traversal, "module": module, "delete":true},
             function (data) {
              location.reload();
            });
    });

    $('.module-add').click(function(event) {
      $.post("/updateProfile", {"profileName": profileName, "module": event.currentTarget.getAttribute('data')},
             function (data) {
              location.reload();
            }).fail(function(e) {
              data = JSON.parse(e.responseText);
              alert( data.error );
            });
    });

    $('.traversal-add').click(function(event) {
      $.post("/updateProfile", {"profileName": profileName, "traversal": event.currentTarget.getAttribute('data')},
             function (data) {
              location.reload();
            });
    });



    $('.button-collapse').sideNav();

    $('.profile-delete .delete').click(function (event){ 
      $.post("/deleteProfile", {"profileName":$('#md1 #filename').val()},
             function (data) {
              location.reload();
            });
    });

    $('.profile .add').click(function (event) {
      var name = $('.profile #name').val();
      if (name.trim().length !== 0) {
        $.post("/addProfile", {"profileName": name},
               function (data) {
                location.reload();
              })
        $('.profile #name').val("");
      }
    });

    /*
     * This is the start of CRUD javascript implementation for modules
     */
     $('.ok').click(function (event) {
      filename = $('#edit #name').html();
      $('#edit').closeModal();
      content = editor.getValue();
      if (filename == "Add a new module") {
        $.post("/addModule",
               {"source_code":content},
               function (data) {
                location.reload();
              });
      } else {
        $.post("/editModule",
               {"filename":filename,"source_code":content},
               function (data) {
                location.reload();
              });
      }
    });

     $('.modules .add').click(function (event) {
      $('#edit #name').html("Add a new module");
      $('#edit .ok').html("Add");
      $('#edit').openModal();
      editor.focus();
      editor.getDoc().setValue(`from Visitor.Visitor import Visitor
from Model.Node import *
name = "Module Name"
prereq = None
class ModuleName(Visitor):
  def __init__(self):
    pass`);
    });

     $('.delete-confirm').click(function (event) {
      $('#md1').openModal();
      $('#md1 #filename').val(event.currentTarget.parentElement.parentElement.id);
    });

     $('.module-delete .delete').click(function (event){ 
      $.post("/deleteModule", {"filename":$('#md1 #filename').val()},
             function (data) {
              location.reload();
            });
    });

     $('.edit').click(function (event) {
      $.post("/getModuleInfo", {"filename":event.currentTarget.parentElement.parentElement.id},
             function (data) {
              $('#edit #name').html(event.currentTarget.parentElement.parentElement.id);
              $('#edit .ok').html("Edit");
              data = JSON.parse(data);
              $('#edit').openModal();
              editor.focus();
              editor.getDoc().setValue(data.content);
            });
    });

    /*
     * This function is used by analyzer page to handle AJAX call to analysis API.
     */

     $('.form').submit(function (event) {
      $('.progress').show();
      $('.navig').hide();
      $('.module-select').hide();
      $('.stats').html("");
      csrf_token = $('#csrf_token').val();
      code = $('#flask-codemirror-source_code').val();
      profile = $('#profile').val();
      $.post("/analyze",
             {"csrf_token":csrf_token,"source_code":code,"profile":profile},
             function (data) {
              $('.progress').hide();
              $('.navig').show();
              $('ul.tabs').tabs('select_tab', 'code');
              data = JSON.parse(data);
              updateStats(data.timetaken,data.sinks.length);
              showModules(data.profile,data);
              updateState(data.sinks);
              $('#graph').html(data.graph);
            }).fail(function(e) {
              $('.progress').hide();
              data = JSON.parse(e.responseText);
              alert( data.error );
            });
            event.preventDefault();
          });
  }); // end of document ready
})(jQuery); // end of jQuery name space