import DataTable from "datatables.net-bs4";
import "datatables.net-responsive-bs4";
import "datatables.net-rowgroup";

import french from "datatables.net-plugins/i18n/fr-FR.mjs";


const createTable = (table, config, options, callback) => {
    return new Promise((resolve, reject) => {
        const data = table.data();
        let settings = {
            language: french,
            responsive: true
        }
        // initialize DOM string
        let dom = '';
        settings = $.extend({}, settings, data, config);
        if (settings.buttons) {
            dom += "<'row px-4 float-right'B>";
        }
        if (settings.searchBuilder) {
            dom += "Q";
        }
        if (settings.searchPanes) {
            dom += "P";
        }
        if (settings.searching !== false || settings.lengthChange !== false) {
            dom += "<'row px-2'";
            if (settings.searching !== false) {
                dom += "<'" + (settings.lengthChange !== false ? "col-sm-6 col-md-8" : "col-sm-12") + "'f>";
            }
            if (settings.lengthChange !== false) {
                dom += "<'" + (settings.searching !== false ? "col-sm-6 col-md-4" : "col-sm-12") + "'l>";
            }
            dom += ">";
        }
        dom += "<'row'<'col-sm-12'tr>>";
        if (settings.info !== false || settings.paging !== false) {
            dom += "<'row px-2 py-1'";
            if (settings.info !== false) {
                dom += "<'col-sm-12 " + (settings.paging !== false ? "col-md-5" : "") + "'i>";
            }
            if (settings.paging !== false) {
                dom += "<'col-sm-12 " + (settings.info !== false ? "col-md-7" : "") + "'p>";
            }
            dom += ">"
        }
        settings.dom = dom;
        // initialize sorting
        let order = data.amsDatatableOrder || data.amsOrder;
        if (typeof order === 'string') {
            const orders = order.split(';');
            order = [];
            for (const col of orders) {
                const colOrder = col.split(',');
                colOrder[0] = parseInt(colOrder[0]);
                order.push(colOrder);
            }
        }
        if (order) {
            settings.order = order;
        }
        // initialize columns
        const
            heads = $('thead th', table),
            columns = [];
        heads.each((idx, th) => {
            columns[idx] = $(th).data('ams-column') || {};
        });
        const sortables = heads.listattr('data-ams-sortable');
        for (const iterator of sortables.entries()) {
            const [idx, sortable] = iterator;
            if (data.rowReorder) {
                columns[idx].sortable = false;
            } else if (sortable !== undefined) {
                columns[idx].sortable =
                    typeof sortable === 'string' ? JSON.parse(sortable) : sortable;
            }
        }
        const types = heads.listattr('data-ams-type');
        for (const iterator of types.entries()) {
            const [idx, stype] = iterator;
            if (stype !== undefined) {
                columns[idx].type = stype;
            }
        }
        settings.columns = columns;
        // initialize table
        settings = $.extend({}, settings, options);
        table.trigger('datatable.init', [table, settings]);
        const instance = new DataTable(`#${table.attr('id')}`, settings);
        table.trigger('datatable.finishing', [table, instance, settings]);
        if (callback) {
            callback(instance, settings);
        }
        if (settings.responsive) {
            setTimeout(() => {
                instance.responsive.rebuild();
                instance.responsive.recalc();
            }, 100);
        }
        table.trigger('datatable.finished', [table, instance, settings]);
        resolve(table);
    })
};


const PyAMS_datatable = {

    init: (tables, options, callback) => {

        // Add autodetect formats
        const types = DataTable.ext.type;

        types.detect.unshift((data) => {
            if (data !== null && data.match(/^(0[1-9]|[1-2][0-9]|3[0-1])\/(0[1-9]|1[0-2])\/[0-3][0-9]{3}$/)) {
                return 'date-euro';
            }
            return null;
        });

        types.detect.unshift((data) => {
            if (data !== null && data.match(/^(0[1-9]|[1-2][0-9]|3[0-1])\/(0[1-9]|1[0-2])\/[0-3][0-9]{3} - ([0-1][0-9]|2[0-3]):[0-5][0-9]$/)) {
                return 'datetime-euro';
            }
            return null;
        });

        // Add sorting methods
        $.extend(types.order, {

            // numeric values using commas separators
            "numeric-comma-asc": (a, b) => {
                let x = a.replace(/,/, ".").replace(/ /g, '');
                let y = b.replace(/,/, ".").replace(/ /g, '');
                x = parseFloat(x);
                y = parseFloat(y);
                return ((x < y) ? -1 : ((x > y) ? 1 : 0));
            },
            "numeric-comma-desc": (a, b) => {
                let x = a.replace(/,/, ".").replace(/ /g, '');
                let y = b.replace(/,/, ".").replace(/ /g, '');
                x = parseFloat(x);
                y = parseFloat(y);
                return ((x < y) ? 1 : ((x > y) ? -1 : 0));
            },

            // date-euro column sorter
            "date-euro-pre": (a) => {
                const trimmed = $.trim(a);
                let x;
                if (trimmed !== '') {
                    const frDate = trimmed.split('/');
                    x = (frDate[2] + frDate[1] + frDate[0]) * 1;
                } else {
                    x = 10000000; // = l'an 1000 ...
                }
                return x;
            },
            "date-euro-asc": (a, b) => {
                return a - b;
            },
            "date-euro-desc": (a, b) => {
                return b - a;
            },

            // datetime-euro column sorter
            "datetime-euro-pre": (a) => {
                const trimmed = $.trim(a);
                let x;
                if (trimmed !== '') {
                    const frDateTime = trimmed.split(' - ');
                    const frDate = frDateTime[0].split('/');
                    const frTime = frDateTime[1].split(':');
                    x = (frDate[2] + frDate[1] + frDate[0] + frTime[0] + frTime[1]) * 1;
                } else {
                    x = 100000000000; // = l'an 1000 ...
                }
                return x;
            },
            "datetime-euro-asc": (a, b) => {
                return a - b;
            },
            "datetime-euro-desc": (a, b) => {
                return b - a;
            }
        });

        Promise.all([
            import('datatables.net-bs4/css/dataTables.bootstrap4.css'),
            import('datatables.net-responsive-bs4/css/responsive.bootstrap4.css')
        ]).then(() => {
            const $tables = $.map(tables, (elt) => {
                return new Promise((resolve, reject) => {
                    const
                        table = $(elt),
                        data = table.data(),
                        config = data.config;
                    resolve(createTable(table, config, options, callback));
                })
            });
            $.when.apply($, $tables).then();
        });
    }
}


export default PyAMS_datatable;
