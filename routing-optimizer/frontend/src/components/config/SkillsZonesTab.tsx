/**
 * Skills & Zones Tab
 */
import React, { useState } from 'react';
import { useConfiguration } from '../../contexts/ConfigurationContext';
import { SkillDefinition, ZoneDefinition } from '../../types/models';

const SkillsZonesTab: React.FC = () => {
  const { skills, addSkill, deleteSkill, zones, addZone, deleteZone } = useConfiguration();
  const [activeSection, setActiveSection] = useState<'skills' | 'zones'>('skills');
  
  // Skills Form
  const [showSkillForm, setShowSkillForm] = useState(false);
  const [skillForm, setSkillForm] = useState({ name: '', description: '', icon: '🔧' });

  // Zones Form
  const [showZoneForm, setShowZoneForm] = useState(false);
  const [zoneForm, setZoneForm] = useState({ name: '', description: '', restrictions: [] as string[] });

  const handleAddSkill = (e: React.FormEvent) => {
    e.preventDefault();
    addSkill({
      id: `skill-${Date.now()}`,
      name: skillForm.name,
      description: skillForm.description,
      icon: skillForm.icon
    });
    setSkillForm({ name: '', description: '', icon: '🔧' });
    setShowSkillForm(false);
  };

  const handleAddZone = (e: React.FormEvent) => {
    e.preventDefault();
    addZone({
      id: `zone-${Date.now()}`,
      name: zoneForm.name,
      description: zoneForm.description,
      restrictions: zoneForm.restrictions
    });
    setZoneForm({ name: '', description: '', restrictions: [] });
    setShowZoneForm(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">🏷️ Skills & Zone</h2>
        <p className="text-sm text-gray-600">Definisci skills veicoli e zone con restrizioni</p>
      </div>

      {/* Section Switcher */}
      <div className="flex gap-2">
        <button
          onClick={() => setActiveSection('skills')}
          className={`px-4 py-2 rounded-md font-semibold ${activeSection === 'skills' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}
        >
          🔧 Skills ({skills.length})
        </button>
        <button
          onClick={() => setActiveSection('zones')}
          className={`px-4 py-2 rounded-md font-semibold ${activeSection === 'zones' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700'}`}
        >
          🗺️ Zone ({zones.length})
        </button>
      </div>

      {/* Skills Section */}
      {activeSection === 'skills' && (
        <div className="space-y-4">
          <button onClick={() => setShowSkillForm(true)} className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">➕ Nuova Skill</button>

          {showSkillForm && (
            <div className="bg-gray-50 p-4 rounded-md border">
              <form onSubmit={handleAddSkill} className="space-y-3">
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-sm font-medium mb-1">Icona</label>
                    <input type="text" value={skillForm.icon} onChange={e => setSkillForm({...skillForm, icon: e.target.value})} className="w-full px-3 py-2 border rounded-md text-center text-2xl" />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-1">Nome Skill *</label>
                    <input type="text" required value={skillForm.name} onChange={e => setSkillForm({...skillForm, name: e.target.value})} placeholder="es. Frigo, Sponda, ADR" className="w-full px-3 py-2 border rounded-md" />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Descrizione</label>
                  <input type="text" value={skillForm.description} onChange={e => setSkillForm({...skillForm, description: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div className="flex gap-2">
                  <button type="button" onClick={() => setShowSkillForm(false)} className="px-4 py-2 border rounded-md">Annulla</button>
                  <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-md">➕ Aggiungi</button>
                </div>
              </form>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {skills.map(skill => (
              <div key={skill.id} className="bg-white border rounded-md p-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{skill.icon}</span>
                  <div>
                    <div className="font-semibold text-sm">{skill.name}</div>
                    {skill.description && <div className="text-xs text-gray-600">{skill.description}</div>}
                  </div>
                </div>
                <button onClick={() => confirm(`Eliminare skill "${skill.name}"?`) && deleteSkill(skill.id)} className="text-red-600 hover:bg-red-50 p-1 rounded">🗑️</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Zones Section */}
      {activeSection === 'zones' && (
        <div className="space-y-4">
          <button onClick={() => setShowZoneForm(true)} className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">➕ Nuova Zona</button>

          {showZoneForm && (
            <div className="bg-gray-50 p-4 rounded-md border">
              <form onSubmit={handleAddZone} className="space-y-3">
                <div>
                  <label className="block text-sm font-medium mb-1">Nome Zona *</label>
                  <input type="text" required value={zoneForm.name} onChange={e => setZoneForm({...zoneForm, name: e.target.value})} placeholder="es. Centro Storico, ZTL, Area Portuale" className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Descrizione</label>
                  <textarea value={zoneForm.description} onChange={e => setZoneForm({...zoneForm, description: e.target.value})} className="w-full px-3 py-2 border rounded-md" rows={2} />
                </div>
                <div className="flex gap-2">
                  <button type="button" onClick={() => setShowZoneForm(false)} className="px-4 py-2 border rounded-md">Annulla</button>
                  <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-md">➕ Aggiungi</button>
                </div>
              </form>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {zones.map(zone => (
              <div key={zone.id} className="bg-white border rounded-md p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-bold text-gray-800">🗺️ {zone.name}</h3>
                  <button onClick={() => confirm(`Eliminare zona "${zone.name}"?`) && deleteZone(zone.id)} className="text-red-600 hover:bg-red-50 p-1 rounded">🗑️</button>
                </div>
                {zone.description && <p className="text-sm text-gray-600">{zone.description}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SkillsZonesTab;
