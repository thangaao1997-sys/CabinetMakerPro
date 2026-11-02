require 'sketchup.rb'
require_relative 'inventory'
module AIIDEAWorkshop
  unless @inventory_menu_registered
    UI.menu('Extensions').add_item('AI IDEA - Export workshop inventory (READ ONLY)') { Inventory.run_gui }
    @inventory_menu_registered=true
  end
end
