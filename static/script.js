$('.like_button').on('click', function() {
    $(this).toggleClass('active');

    if ($(this).hasClass('active')) {
        var text = $(this).data('btn btn-info');
    } else {
        var text = $(this).data('btn btn-outline-info');
    }

    $(this).html(text);

    event.preventDefault();

    console.log(url);
    $.ajax({
        url: '/like',
        type: 'POST',
        dataType: 'text',
        data: {
            id: $(this).val()
        }
    }).done(function() {
        console.log('success');
    }).fail(function() {
        console.log('fail');
    })
})

$('.delete_button ').on('click ', function() {
    flag = window.confirm("本当に削除してもよろしいでしょうか？")
    event.preventDefault();
    if (flag === true) {
        url = '/delete?id=' + $(this).val();
        $.ajax({
            url: url,
            type: 'GET',
            dataType: 'text',

        })
    }
})

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