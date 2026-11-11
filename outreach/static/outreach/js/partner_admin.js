
document.addEventListener("DOMContentLoaded", function () {
    const partnerType = document.getElementById("id_partner_type");

    if (!partnerType) {
        return;
    }

    const schedulingFields = [
        "scheduling_type",
        "priority"
    ];

    const schedulingSection = document.querySelector(
        "fieldset"
    );

    function updatePartnerForm() {
        const isAdHoc = partnerType.value === "AD_HOC";

        schedulingFields.forEach(function (fieldName) {
            const field = document.getElementById("id_" + fieldName);

            if (!field) {
                return;
            }

            const row = field.closest(".form-row");

            if (row) {
                row.style.display = isAdHoc ? "none" : "";
            }
        });

        document.querySelectorAll("fieldset").forEach(function (fieldset) {
            const heading = fieldset.querySelector("h2");

            if (
                heading &&
                heading.textContent.trim() === "Scheduling Rules"
            ) {
                fieldset.style.display = isAdHoc ? "none" : "";
            }
        });
    }

    partnerType.addEventListener("change", updatePartnerForm);

    updatePartnerForm();
});
