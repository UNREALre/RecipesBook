$("document").ready(function(){
    $(".js--add-ingr").on("click", function(e){
        e.preventDefault();
        var item = $(".f-row.ingredient").eq(0).clone();
        item.find("input").val("");
        $(".js--dynamic-ingr-wrapper").append(item);
        fireIngrEvents();
    });

    $(".js--confirm-delete").on("click", function(e){
       e.preventDefault();
       if (confirm($(this).data("conftext"))) {
           window.location = $(this).attr("href");
       }
    });

    $(".js--share-recipe").on("click", function(e){
        e.preventDefault();
        $(".js--share-wrapper").toggle();
    });

    $(".js--add-to-fav").on("click", function(e){
        e.preventDefault();
        $.post($(this).attr("href"), {})
            .done(function(msg){
                $("#modal_action").find(".description").html(msg.ok);
                $("#modal_action").modal();
            })
            .fail(function(xhr, status, error) {
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    $("#modal_error").find(".description").html(xhr.responseJSON.error);
                }
                $("#modal_error").modal();
            });
    });
});

function fireIngrEvents() {
    $(".js--remove-ingr").on("click", function(e){
        e.preventDefault();
        $(this).parents(".f-row.ingredient").eq(0).remove();
    });
}