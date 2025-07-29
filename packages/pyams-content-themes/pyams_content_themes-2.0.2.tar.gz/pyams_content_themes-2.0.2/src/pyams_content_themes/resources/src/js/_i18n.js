
import MyAMS from './_utils';

const PyAMS_i18n = {

    BTN_CLOSE: "Close",

    SUCCESS: "Action successful",

    ERROR_OCCURRED: "An error occurred!",
    ERRORS_OCCURRED: "Some errors occurred!"
}


MyAMS.i18n = PyAMS_i18n;

const lang = $('html').attr('lang');
import(`./i18n/${lang}.js`).then((module) => {
    const i18n = module.default;
    $.extend(MyAMS.i18n, i18n);
});
