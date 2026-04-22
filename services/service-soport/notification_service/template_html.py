html_template = """
<div style="font-family: Arial; background-color:#f4f4f4; padding:20px;">

    <div style="max-width:600px; margin:auto; background:white; border-radius:8px; overflow:hidden;">

        <!-- Header -->
        <div style="background:#0d6efd; color:white; padding:15px 20px; font-size:20px; font-weight:bold;">
            TravelHub
        </div>

        <!-- Contenido -->
        <div style="padding:20px;">
            <h2 style="color:#333;">🔔 Notificación</h2>

            <p style="font-size:16px; color:#555;">
                {{mensaje}}
            </p>

            <hr style="margin-top:20px;">
            <p style="font-size:12px; color:#999;">
                Este mensaje fue generado automáticamente por TravelHub.
            </p>
        </div>

    </div>

</div>
"""

