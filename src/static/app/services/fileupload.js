MatchingApp.service('Fileupload', function(){
  this.init = function(files, options){

    function scriptsLoaded(data) {
        $('#fileupload').ready(function(){
          var $form = $('#fileupload');

          $form.fileupload('option', 'done').call($form, $.Event('done'), { result: { files: files } })

          $form.on('click', '.paper-title', function(e){
            e.preventDefault();

            var title = $(this).attr('data-title');
            var key = $(this).attr('data-key');

            options.fileClicked({
              title: title,
              key: key
            });
          });

          $form.bind('fileuploadsubmit', function (e, data) {
              var inputs = data.context.find(':input');
              if (inputs.filter(function () {
                          return !this.value && $(this).prop('required');
                      }).first().focus().length) {
                  data.context.find('button').prop('disabled', false);
                  return false;
              }

              data.formData = inputs.serializeArray();
          });
        });
    }

    function downloadTemplateLoaded(data) {
        window.downloadTemplate = data;
        $('#ajax-load-scripts').load('static/scripts.html', scriptsLoaded);
    }

    function uploadTemplateLoaded(data) {
        window.uploadTemplate = data;
        $.get('static/template-download.tmpl', downloadTemplateLoaded);
    }

    $(function () {
        $.get('static/template-upload.tmpl', uploadTemplateLoaded);
    });
  };

  this.updateFile = function(file){
    var $fileEl = $('#fileupload').find('a[data-key=' + file.key + ']');

    $fileEl.html(file.title);
    $fileEl.removeAttr('data-title');
    $fileEl.attr('data-title', file.title);
  };
});
