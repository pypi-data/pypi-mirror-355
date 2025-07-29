

import { Calendar } from "@fullcalendar/core";
import dayGridPlugin from "@fullcalendar/daygrid";
import listPlugin from "@fullcalendar/list";
import interactionPlugin from "@fullcalendar/interaction";
import bootstrapPlugin from '@fullcalendar/bootstrap';


const isSmallDevice = () => {
    return (window.innerWidth < 768);
};


const createCalendar = (calendar, config, options, callback) => {
    return new Promise((resolve, reject) => {
        const data = calendar.data();
        let settings = {
            plugins: [
                interactionPlugin,
                dayGridPlugin,
                listPlugin,
                bootstrapPlugin
            ],
            initialView: isSmallDevice() ? 'listMonth': 'dayGridMonth',
            themeSystem: 'bootstrap',
            locale: $('html').attr('lang'),
            headerToolbar: {
                start: 'title',
                center: 'today',
                right: 'prev,next'
            },
            bootstrapFontAwesome: {
                prev: 'fa-chevron-left',
                next: 'fa-chevron-right'
            },
            firstDay: 1,
            weekNumberCalculation: 'ISO',
            eventDidMount: PyAMS_calendar.mountedEvent,
            eventClick: PyAMS_calendar.clickEvent
        }
        settings = $.extend({}, settings, config, options);
        calendar.trigger('calendar.init', [calendar, settings]);
        const instance = new Calendar(calendar.get(0), settings);
        calendar.trigger('calendar.finishing', [calendar, instance, settings]);
        if (callback) {
            callback(instance, config);
        }
        calendar.trigger('calendar.finished', [calendar, instance, settings]);
        instance.render();
        resolve(instance);
    });
};


const PyAMS_calendar = {

    init: (calendars, options, callback) => {
        const $calendars = $.map(calendars, (elt) => {
            return new Promise((resolve, reject) => {
                const
                    calendar = $(elt),
                    data = calendar.data(),
                    config = data.calendarConfig;
                if (config) {
                    resolve(createCalendar(calendar, config, options, callback));
                } else {
                    $.get(data.calendarUrl || 'get-calendar-configuration.json', (config) => {
                        resolve(createCalendar(calendar, config, options, callback));
                    });
                }
            });
        });
        $.when.apply($, $calendars).then();
    },

    mountedEvent: (info) => {
        const
            elt = $(info.el),
            lang = $('html').attr('lang'),
            startDate = new Intl.DateTimeFormat(lang, {
                hour: '2-digit',
                minute: '2-digit'
            }).format(info.event.start);
        elt.tooltip({
            title: `${startDate} - ${info.event.title}`
        });
    },

    clickEvent: (info) => {
        const
            event = info.event,
            href = event.extendedProps?.href;
        if (href) {
            window.location.href = href;
        }
    }
};


export default PyAMS_calendar;
