
import flet as ft
import asyncio

try:
    from jnius import autoclass
    from escpos.printer import Dummy
    IS_PYJNIUS_AVAILABLE = True
except ImportError:
    IS_PYJNIUS_AVAILABLE = False
    Dummy = None

# Standard Bluetooth SPP UUID for thermal printers
UUID = "00001101-0000-1000-8000-00805F9B34FB"

def generate_receipt():
    if not IS_PYJNIUS_AVAILABLE or Dummy is None:
        return b"(TEST RECEIPT)\nApple x2 $4.00\nBanana x5 $7.50\nOrange x3 $6.00\nTOTAL $17.50\n"
    p = Dummy()
    p.set(align='center')
    p.text("SPEED X STORE\n")
    p.text("-------------------\n")
    p.text("Item            Price\n")
    p.text("----------------------\n")
    p.text("Apple x2      $4.00\n")
    p.text("Banana x5     $7.50\n")
    p.text("Orange x3     $6.00\n")
    p.text("----------------------\n")
    p.text("TOTAL:       $17.50\n")
    p.text("======================\n")
    p.text("Thank you! Come again\n\n\n")
    p.cut()
    return p.output

def list_paired_devices():
    if not IS_PYJNIUS_AVAILABLE:
        return [("Dummy Printer", "00:11:22:33:44:55")]
    try:
        BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        adapter = BluetoothAdapter.getDefaultAdapter()
        if adapter is None or not adapter.isEnabled():
            return []
        paired_devices = adapter.getBondedDevices().toArray()
        return [(d.getName(), d.getAddress()) for d in paired_devices]
    except Exception as ex:
        return [(f"Error: {str(ex)}", "")]

def print_to_device(device_name):
    if not IS_PYJNIUS_AVAILABLE:
        return f"(TEST MODE) Printed to {device_name}"
    try:
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
            return f"Device '{device_name}' not found. Please pair it first."
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
    except Exception as ex:
        return f"Error: {str(ex)}"

def main(page: ft.Page):
    page.title = "Bluetooth Receipt Printer"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    status = ft.Text("Status: Ready")
    devices = list_paired_devices()
    auto_selected_printer = "Printer" if any(d[0] == "Printer" for d in devices) else None
    device_dropdown = ft.Dropdown(
        label="Select Printer",
        width=300,
        options=[ft.dropdown.Option(d[0]) for d in devices],
        value=auto_selected_printer,
        visible=len(devices) > 1 or not auto_selected_printer
    )

    def on_print(e):
        try:
            selected_device = device_dropdown.value if device_dropdown.visible else auto_selected_printer
            if not selected_device:
                status.value = "Please select a printer first."
            else:
                status.value = print_to_device(selected_device)
        except Exception as ex:
            status.value = f"Error: {str(ex)}"
        page.update()

    def check_permissions(e):
        if IS_PYJNIUS_AVAILABLE:
            try:
                Activity = autoclass("android.app.Activity")
                ContextCompat = autoclass("androidx.core.content.ContextCompat")
                Permission = autoclass("android.Manifest$permission")
                activity_host_class = autoclass("org.flet.fletapp.FletActivity")
                activity = activity_host_class.mActivity
                if ContextCompat.checkSelfPermission(activity, Permission.BLUETOOTH_CONNECT) != 0:
                    activity.requestPermissions([Permission.BLUETOOTH_CONNECT], 1000)
                    status.value = "Requesting Bluetooth permission..."
                else:
                    status.value = "Status: Ready"
            except Exception as ex:
                status.value = f"Permission check error: {str(ex)}"
        page.update()

    page.on_resume = check_permissions  # Check permissions when app resumes
    page.add(
        ft.Column([
            ft.Text("Bluetooth Receipt Printer", size=20, weight="bold"),
            device_dropdown,
            ft.ElevatedButton("Print Dummy Receipt", on_click=on_print),
            status
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        ft.app(target=main)
    finally:
        loop.close()
