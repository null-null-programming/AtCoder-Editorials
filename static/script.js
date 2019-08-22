//input内でのEnter無効化
$(function() {
    $(document).on("keypress", "input:not(.allow_submit)", function(event) {
        return event.which !== 13;
    });
});

var csrftoken = $('meta[name=csrf-token]').attr('content')

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken)
        }
    }
})