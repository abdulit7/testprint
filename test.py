import flet as ft
from jnius import autoclass
from escpos.printer import Dummy

# Standard Bluetooth SPP UUID for thermal printers
UUID = "00001101-0000-1000-8000-00805F9B34FB"

def generate_receipt():
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

def print_to_bt600m():
    BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
    adapter = BluetoothAdapter.getDefaultAdapter()
    if adapter is None:
        return "Bluetooth not supported."
    if not adapter.isEnabled():
        return "Bluetooth is disabled. Please enable it."

    # Find printer
    paired_devices = adapter.getBondedDevices().toArray()
    target_device = None
    for d in paired_devices:
        if d.getName() == "BT-600M":
            target_device = d
            break

    if not target_device:
        return "Printer BT-600M not found. Please pair it first."

    # Connect to printer
    UUIDClass = autoclass("java.util.UUID")
    uuid = UUIDClass.fromString(UUID)
    socket = target_device.createRfcommSocketToServiceRecord(uuid)
    socket.connect()

    # Send receipt data
    output_stream = socket.getOutputStream()
    data = generate_receipt()
    output_stream.write(data)
    output_stream.flush()
    socket.close()

    return "Receipt printed successfully!"

def main(page: ft.Page):
    status = ft.Text("Status: Ready")

    def on_print(e):
        if page.platform == "android":
            status.value = print_to_bt600m()
        else:
            status.value = "Printing only works on Android device."
        page.update()

    page.add(
        ft.Column([
            ft.Text("Bluetooth Receipt Printer"),
            ft.ElevatedButton("Print Dummy Receipt", on_click=on_print),
            status
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)
