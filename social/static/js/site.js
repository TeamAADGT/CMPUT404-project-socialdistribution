$(document).ready(function () {

    /* Shorten Text */
    function shortenText() {
        $(document).ready(function () {
            $(".sd-comment-text").shorten({
                moreText: 'Read more',
                lessText: 'Read less'
            });

            $(".sd-comment-text-small").shorten({showChars: 10});

        });
    }

    shortenText();

    function addAuthorFields() {
        var maxFields = 10; // Max number of authors that can be added
        var count = 1;

        var $wrapper = $("#sd-select-authors-container");

        $wrapper.on("click", ".btn-add", function (e) {

            e.preventDefault();

            if (count < maxFields) {
                count++;

                var $content = $("#sd-select-authors-container");
                var $currentItem = $(this).parents(".sd-author-item:first");
                var $newItem = $currentItem.clone().appendTo($content);

                // Clear input fields
                $newItem.find("input").val("");

                $content.find(".sd-author-item:not(:last) .glyphicon")
                    .removeClass("glyphicon-plus")
                    .addClass("glyphicon-minus");

                $content.find(".sd-author-item:not(:last) .btn-add")
                    .removeClass("btn-add").addClass("btn-remove")
                    .removeClass("btn-success").addClass("btn-danger");

                //Give an id to the accessory
                $content.find(".sd-author-item:last")
                    .attr("id", "sd-author-item" + count);
            }

        }).on("click", ".btn-remove", function (e) {
            count--;
            $(this).parents(".sd-author-item:first").remove();

            e.preventDefault();
            return false;
        });
    }

    /* Show window for users that post is going to be visible to */
    function postVisibleTo() {
        $("#id_visible_to").parent(".form-group").css("display", "none");

        $("select#id_visibility")
            .change(function () {
                var str = "";
                $("select#id_visibility option:selected").each(function () {
                    str += $(this).text();
                    if (str === "Private") {
                        $("#id_visible_to").parent(".form-group").show("slow");

                    }
                    else {
                        $("#id_visible_to").parent(".form-group").css("display", "none");
                    }
                });
            })
            .change();
    }

    //postVisibleTo();

    /* Show window for users that post is going to be visible to */
    function postVisibleTo2() {
        $("#sd-select-authors-container").hide();

        $("select#id_visibility")
            .change(function () {
                var str = "";
                $("select#id_visibility option:selected").each(function () {
                    str += $(this).text();
                    if (str === "Private") {
                        $("#sd-select-authors-container").show("slow");

                        addAuthorFields();
                    }
                    else {
                        $("#sd-select-authors-container").hide("slow");
                    }
                });
            })
            .change();
    }

    postVisibleTo2();
});



