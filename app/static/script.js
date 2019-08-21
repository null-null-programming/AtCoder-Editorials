(async function() {

    const contestName = [];
    $.ajax({
        type: 'GET',
        url: 'https://kenkoooo.com/atcoder/resources/contests.json',
        dataType: 'json',
        success: function(json) {
            var len = json.length;
            for (var i = 0; i < len; i++) {
                contestName.push(json[i].title);
            }
        }
    });

    //検索候補を表示する。
    $('#autocomplete_search').autocomplete({
        source: contestName,
        autoFocus: true,
        delay: 100,
        minLength: 2,
        appendTo: "menu",

        //候補をクリックすることでsubmitできるようにする
        select: function(event, ui) {
            $("#autocomplete_search").val(ui.item.label);
            $("#search").submit();
        }
    });

})();

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