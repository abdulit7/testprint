import flet as ft

try:
    from jnius import autoclass
    from escpos.printer import Dummy
except ImportError:
    autoclass = None
    Dummy = None


UUID = "00001101-0000-1000-8000-00805F9B34FB"


def generate_receipt():
    if Dummy is None:
        return b"(TEST RECEIPT)\nApple x2 $4.00\nBanana x5 $7.50\nOrange x3 $6.00\nTOTAL $17.50\n"
    p = Dummy()
    p.text("   SPEED X STORE\n")
    p.text("  -------------------\n")
    p.text("Item            Price\n")
    p.text("----------------------\n")
    p.text("Apple x2      $4.00\n")
    p.text("Banana x5     $7.50\n")
    p.text("Orange x3     $6.00\n")
    p.text("----------------------\n")
    p.text("TOTAL:       $17.50\n")
    p.text("======================\n")
    p.text(" Thank you! Come again\n\n\n")
    p.cut()
    return p.output


def list_paired_devices(is_android=False):
    if not is_android or autoclass is None:
        # Safe fallback on Windows
        return [("Dummy Printer", "00:11:22:33:44:55")]

    BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
    adapter = BluetoothAdapter.getDefaultAdapter()
    if adapter is None or not adapter.isEnabled():
        return []
    paired_devices = adapter.getBondedDevices().toArray()
    return [(d.getName(), d.getAddress()) for d in paired_devices]


def print_to_device(device_name, is_android=False):
    if not is_android or autoclass is None:
        return f"(TEST MODE) Printed to {device_name}"

    BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
    adapter = BluetoothAdapter.getDefaultAdapter()
    if adapter is None:
        return "Bluetooth not supported."
    if not adapter.isEnabled():
        return "Bluetooth is disabled. Please enable it."

    paired_devices = adapter.getBondedDevices().toArray()
    target_device = None
    for d in paired_devices:
        if d.getName() == device_name:
            target_device = d
            break

    if not target_device:
        return f"Device '{device_name}' not found."

    UUIDClass = autoclass("java.util.UUID")
    uuid = UUIDClass.fromString(UUID)
    socket = target_device.createRfcommSocketToServiceRecord(uuid)
    socket.connect()

    output_stream = socket.getOutputStream()
    data = generate_receipt()
    output_stream.write(data)
    output_stream.flush()
    socket.close()

    return "Receipt printed successfully!"


def main(page: ft.Page):
    is_android = page.platform == "android"
    status = ft.Text("Status: Ready")

    devices = list_paired_devices(is_android)
    device_dropdown = ft.Dropdown(
        label="Select Printer",
        width=300,
        options=[ft.dropdown.Option(d[0]) for d in devices],
    )

    def on_print(e):
        try:
            if not device_dropdown.value:
                status.value = "Please select a printer first."
            else:
                status.value = print_to_device(device_dropdown.value, is_android)
        except Exception as ex:
            status.value = f"Error: {ex}"
        page.update()

    page.add(
        ft.Column(
            [
                ft.Text("Bluetooth Receipt Printer", size=20, weight="bold"),
                device_dropdown,
                ft.ElevatedButton("Print Dummy Receipt", on_click=on_print),
                status,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


ft.app(target=main)
