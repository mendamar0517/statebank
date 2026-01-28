/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
const { Component, onWillStart, useState, useRef } = owl;

export class ProfileDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.chartRef = useRef("chart");
        this.state = useState({
            info: {
                menu_hierarchy: {},
                user_info: { name: "", job: "", email: "", dept: "", phone: "", image: false },
                erp_rights: [],
                available_modules: []
            },
            displayedCards: [],
            expandedMenu: null,
            expandedSub: null,
            graphType: 'status',
            activeSub: null,
            palette: ['#6f42c1', '#fd7e14', '#20c997', '#0d6efd', '#d63384', '#198754', '#ffc107']
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            try {
                const data = await this.rpc("/get_profile_dashboard_data");
                if (data) {
                    this.state.info = data;
                    // Хэрэв бичлэгтэй модуль байхгүй бол available_modules-оос эхний 5-ыг авна
                    this.state.displayedCards = data.default_visible && data.default_visible.length > 0
                                                ? [...data.default_visible]
                                                : (data.available_modules ? data.available_modules.slice(0, 5) : []);
                }
            } catch (e) {
                console.error("RPC Error:", e);
            }
        });
    }

    toggleModule(name) {
        if (this.state.displayedCards.includes(name)) {
            this.state.displayedCards = this.state.displayedCards.filter(c => c !== name);
        } else {
            this.state.displayedCards.push(name);
        }
    }

    async toggleSub(sub) {
        if (this.state.expandedSub === sub.id) {
            this.state.expandedSub = null;
        } else {
            this.state.expandedSub = sub.id;
            this.state.activeSub = sub;
            this.state.graphType = sub.has_status ? 'status' : 'participation';
            setTimeout(() => { this.updateChart(); }, 150);
        }
    }

    async updateChart() {
        const canvas = this.chartRef.el;
        if (!canvas || !this.state.activeSub) return;
        const data = await this.rpc("/get_sub_menu_analytics", { res_model: this.state.activeSub.model });
        const chartData = (this.state.graphType === 'status') ? data.status : data.participation;
        if (this.chart) this.chart.destroy();

        this.chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: Object.keys(chartData),
                datasets: [{
                    data: Object.values(chartData),
                    backgroundColor: this.state.palette,
                    borderWidth: 3,
                    borderColor: '#ffffff',
                    hoverOffset: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: { size: 12, weight: '600' },
                            generateLabels: (chart) => {
                                const d = chart.data;
                                return d.labels.map((label, i) => ({
                                    text: `${label}: ${d.datasets[0].data[i]}`,
                                    fillStyle: d.datasets[0].backgroundColor[i],
                                    pointStyle: 'circle',
                                    index: i
                                }));
                            }
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    onProgress: function() {
                        const ctx = this.ctx;
                        ctx.save();
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'middle';
                        this.data.datasets.forEach((dataset, i) => {
                            const meta = this.getDatasetMeta(i);
                            if (meta.data.length > 0) {
                                // 1. Голд нийт тоог зурах
                                const total = dataset.data.reduce((a, b) => a + b, 0);
                                const centerX = meta.data[0].x;
                                const centerY = meta.data[0].y;
                                ctx.fillStyle = "#4B5563";
                                ctx.font = "bold 26px sans-serif";
                                ctx.fillText(total, centerX, centerY - 10);
                                ctx.font = "bold 12px sans-serif";
                                ctx.fillStyle = "#9CA3AF";
                                ctx.fillText("НИЙТ", centerX, centerY + 18);

                                // 2. Сегмент бүр дээрх тоог зурах
                                meta.data.forEach((element, index) => {
                                    const val = dataset.data[index];
                                    if (val > 0) {
                                        const { x, y } = element.tooltipPosition();
                                        ctx.shadowColor = "rgba(0, 0, 0, 0.5)";
                                        ctx.shadowBlur = 4;
                                        ctx.fillStyle = "#ffffff";
                                        ctx.font = "bold 14px sans-serif";
                                        ctx.fillText(val, x, y);
                                        ctx.shadowBlur = 0;
                                    }
                                });
                            }
                        });
                        ctx.restore();
                    }
                }
            }
        });
    }
}
ProfileDashboard.template = "profile.ProfileDashboardMain";
registry.category("actions").add("profile_dashboard_tag", ProfileDashboard);