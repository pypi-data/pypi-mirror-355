
def display_kpi_dashboard(kpis, title=None, subtitle=None, card_width=170, icon_map=None):
    """
    kpis: list of dicts, each with keys 'label', 'value', and optional 'color', 'icon'
    title: Optional title above the cards
    subtitle: Optional subtitle below title
    card_width: width of each card in px
    icon_map: dict (label -> icon unicode/emoji)
    """
    if icon_map is None:
        icon_map = {}

    cards = []
    for kpi in kpis:
        label = kpi.get('label', '')
        value = kpi.get('value', '')
        color = kpi.get('color', '#1976d2')
        icon = kpi.get('icon') or icon_map.get(label, '')
        icon_html = f"<span style='font-size:22px;margin-right:5px'>{icon}</span>" if icon else ""
        html = f"""
        <div style="
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            background: #fff;
            border-left: 7px solid {color};
            border-radius: 14px;
            box-shadow: 0 4px 14px #0002;
            min-width: {card_width}px; max-width: {card_width+30}px;
            margin: 10px 12px 10px 0;
            padding: 18px 16px 12px 16px;
        ">
          <div style="font-size: 16px; color: #444;">{icon_html}{label}</div>
          <div style="font-size: 32px; font-weight: bold; color: {color}; margin-top:10px;">{value}</div>
        </div>
        """
        cards.append(widgets.HTML(html))
    dashboard = widgets.HBox(cards)
    items = []
    if title:
        # Wrap IPython.display.HTML object in ipywidgets.HTML
        items.append(widgets.HTML(f"<h2 style='color:#1976d2;margin-bottom:2px'>{title}</h2>"))
    if subtitle:
        # Wrap IPython.display.HTML object in ipywidgets.HTML
        items.append(widgets.HTML(f"<div style='color:#888;margin-bottom:8px'>{subtitle}</div>"))
    items.append(dashboard)
    display(widgets.VBox(items))