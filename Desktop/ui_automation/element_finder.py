import uiautomation as auto
from typing import List, Optional
from .exceptions import ElementNotFoundError
from .logger import UILogger

class ElementFinder:
    """Discovers UI elements within a parent control recursively."""
    
    def find_element(self, parent: auto.Control, name: str = None, 
                     automation_id: str = None, control_type: str = None, 
                     class_name: str = None, search_depth: int = 5,
                     index: int = 1) -> auto.Control:
        """Locates a single element matching the criteria."""
        
        search_params = {
            "name": name, "automation_id": automation_id, 
            "control_type": control_type, "class_name": class_name, 
            "index": index
        }
        UILogger.log_search("Element", search_params, False)
        
        kwargs = {"searchDepth": search_depth, "foundIndex": index}
        if name: kwargs["Name"] = name
        if automation_id: kwargs["AutomationId"] = automation_id
        if class_name: kwargs["ClassName"] = class_name
        
        # Determine control type method
        if control_type:
            control_type = control_type.lower()
            if 'button' in control_type:
                element = parent.ButtonControl(**kwargs)
            elif 'edit' in control_type or 'text' in control_type:
                element = parent.EditControl(**kwargs)
            elif 'menuitem' in control_type:
                element = parent.MenuItemControl(**kwargs)
            elif 'menu' in control_type:
                element = parent.MenuControl(**kwargs)
            elif 'listitem' in control_type:
                element = parent.ListItemControl(**kwargs)
            elif 'list' in control_type:
                element = parent.ListControl(**kwargs)
            elif 'combo' in control_type:
                element = parent.ComboBoxControl(**kwargs)
            elif 'check' in control_type:
                element = parent.CheckBoxControl(**kwargs)
            elif 'radio' in control_type:
                element = parent.RadioButtonControl(**kwargs)
            elif 'document' in control_type:
                element = parent.DocumentControl(**kwargs)
            else:
                kwargs['ControlTypeName'] = control_type
                element = parent.Control(**kwargs)
        else:
            if not any(k in kwargs for k in ['Name', 'AutomationId', 'ClassName']):
                kwargs['searchDepth'] = search_depth # It needs something, but uiautomation really needs a property.
                pass
            element = parent.Control(**kwargs)
            
        if element.Exists(0, 0):
            UILogger.log_search("Element", search_params, True)
            return element
            
        raise ElementNotFoundError(f"Could not find element: {search_params}")
        
    def find_all_elements(self, parent: auto.Control, name: str = None, 
                     automation_id: str = None, control_type: str = None, 
                     class_name: str = None, search_depth: int = 5) -> List[auto.Control]:
        """Finds all matching elements within the given depth via recursive traversal."""
        matches = []
        if search_depth < 1:
            return matches
            
        try:
            children = parent.GetChildren()
        except Exception:
            return matches
            
        for child in children:
            is_match = True
            if name and child.Name != name:
                is_match = False
            if automation_id and child.AutomationId != automation_id:
                is_match = False
            if class_name and child.ClassName != class_name:
                is_match = False
            if control_type:
                if control_type.lower() not in child.ControlTypeName.lower():
                    is_match = False
                    
            if is_match:
                matches.append(child)
                
            if search_depth > 1:
                matches.extend(self.find_all_elements(
                    child, name, automation_id, control_type, class_name, search_depth - 1
                ))
                
        return matches
