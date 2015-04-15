MatchingApp.service('Fileupload', function(){
  this.init = function(files){
    function scriptsLoaded(data) {

        var $form = $('#fileupload')

        $form.fileupload('option', 'done').call($form, $.Event('done'), { result: { files: files } })

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

        $(document).ready(function () {
            $("#btn-save").click(function () {
                var text = $('#bio-text').val();

                $.ajax({
                    type: 'POST',
                    url: "/update_bio",
                    data: {"bio_new_text": JSON.stringify(text)},
                    dataType: 'json',
                    success: function (data) {
                        window.location.reload(true);
                    }
                });
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
});
